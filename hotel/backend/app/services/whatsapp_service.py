"""WhatsApp Business API entegrasyonu.

Aktif `whatsapp` entegrasyon kaydından parametreleri okur, mesaj gönderir,
gelen webhook'ları parse eder ve basit kural-tabanlı GuestAI bot yanıtı üretir.
İleride LLM tabanlı yanıt için chat_service ile birleştirilir.
"""
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.param_crypto import decrypt_params
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.crm import CommunicationLog
from app.models.front_office import Guest
from app.models.integration_setting import IntegrationSetting

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Meta WhatsApp Cloud API ile mesajlaşma."""

    @staticmethod
    async def _resolve_integration(db: AsyncSession) -> tuple[IntegrationSetting, dict]:
        res = await db.execute(
            select(IntegrationSetting).where(
                IntegrationSetting.integration_type == "whatsapp",
                IntegrationSetting.enabled.is_(True),
                IntegrationSetting.deleted_at.is_(None),
            )
        )
        row = res.scalars().first()
        if row is None:
            raise ValueError("Aktif bir WhatsApp entegrasyonu bulunamadı")
        params = decrypt_params(row.params_encrypted) or {}
        if not params.get("access_token") or not params.get("phone_number_id"):
            raise ValueError("WhatsApp parametreleri eksik (access_token, phone_number_id)")
        return row, params

    @staticmethod
    def verify_webhook_signature(secret: str, payload: bytes, signature_header: str) -> bool:
        """Meta `X-Hub-Signature-256` header'ını doğrular."""
        if not signature_header or not secret:
            return False
        if signature_header.startswith("sha256="):
            signature_header = signature_header[len("sha256=") :]
        digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature_header)

    @classmethod
    async def send_message(
        cls,
        db: AsyncSession,
        to_phone: str,
        text: str,
        guest_id: Optional[UUID] = None,
        mock: bool = True,
    ) -> dict:
        """Tek bir misafire WhatsApp mesajı gönderir. CommunicationLog'a yazar."""
        integration, params = await cls._resolve_integration(db)
        endpoint = (
            f"https://graph.facebook.com/v18.0/{params['phone_number_id']}/messages"
        )
        body = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": text},
        }

        if mock or params.get("environment") == "test":
            external_ref = f"WAMID-MOCK-{secrets.token_hex(8)}"
            ok = True
        else:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        endpoint,
                        headers={"Authorization": f"Bearer {params['access_token']}"},
                        json=body,
                    )
                ok = resp.status_code < 300
                external_ref = (
                    resp.json().get("messages", [{}])[0].get("id", "")
                    if ok
                    else f"ERR-{resp.status_code}"
                )
            except Exception as e:
                logger.exception("WhatsApp gönderim hatası: %s", e)
                ok = False
                external_ref = "ERR-EXC"

        # CommunicationLog kaydı
        if guest_id is None:
            # Telefondan misafir bul
            g_res = await db.execute(select(Guest).where(Guest.phone == to_phone))
            g = g_res.scalars().first()
            if g:
                guest_id = g.id
        if guest_id:
            log = CommunicationLog(
                guest_id=guest_id,
                channel="whatsapp",
                direction="outbound",
                body=text,
                status="delivered" if ok else "failed",
                external_ref=external_ref,
            )
            db.add(log)
            await db.commit()

        return {"success": ok, "external_ref": external_ref}

    # ── Inbound webhook ──

    @staticmethod
    def _bot_reply(text: str) -> Optional[str]:
        """Basit kural-tabanlı GuestAI yanıtı. Eşleşme yoksa None döner (insana devreder)."""
        t = (text or "").lower().strip()
        if not t:
            return None
        if any(k in t for k in ("merhaba", "selam", "hello", "hi")):
            return "Merhaba 👋 Otelimize hoş geldiniz. Size nasıl yardımcı olabilirim?"
        if any(k in t for k in ("check-in", "checkin", "giriş saati")):
            return "Standart check-in saatimiz 14:00, check-out saatimiz 12:00'dir. Erken check-in için resepsiyonumuza danışabilirsiniz."
        if any(k in t for k in ("wifi", "wi-fi", "internet")):
            return "Tüm odalarımızda ücretsiz Wi-Fi mevcuttur. Şifreniz check-in sırasında verilen kartın arkasındadır."
        if any(k in t for k in ("kahvaltı", "kahvalti", "breakfast")):
            return "Açık büfe kahvaltı 07:00–10:30 arası restoranımızda servis edilmektedir."
        if any(k in t for k in ("havaalanı", "transfer", "shuttle")):
            return "Havaalanı transfer hizmetimiz vardır. Tarihinizi yazarsanız rezervasyon oluşturabilirim."
        if any(k in t for k in ("şikayet", "sikayet", "complaint", "problem")):
            return "Yaşadığınız durumu detaylandırırsanız ilgili yöneticimize hemen iletiyorum. Teşekkürler."
        return None

    @classmethod
    async def handle_inbound(cls, db: AsyncSession, message: dict) -> dict:
        """Meta webhook'tan gelen tek mesajı işle.

        message örneği: {"from": "+9055...", "text": {"body": "..."}, "id": "wamid..."}
        """
        from_phone = message.get("from", "")
        text = (message.get("text") or {}).get("body", "")
        wamid = message.get("id", "")

        # Misafiri telefondan eşle
        g_res = await db.execute(select(Guest).where(Guest.phone == from_phone))
        guest = g_res.scalars().first()

        # Inbound log
        if guest:
            db.add(
                CommunicationLog(
                    guest_id=guest.id,
                    channel="whatsapp",
                    direction="inbound",
                    body=text,
                    status="received",
                    external_ref=wamid,
                )
            )

        # Bot yanıtı
        reply = cls._bot_reply(text)
        if reply and guest:
            await db.commit()
            send_result = await cls.send_message(db, from_phone, reply, guest_id=guest.id, mock=True)
            return {"matched_guest": str(guest.id), "auto_reply": reply, "delivery": send_result}

        await db.commit()
        return {
            "matched_guest": str(guest.id) if guest else None,
            "auto_reply": None,
            "delivery": None,
        }
