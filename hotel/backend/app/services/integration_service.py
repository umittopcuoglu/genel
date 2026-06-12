"""
Entegrasyon Ayarları servisi: CRUD + tip bazlı canlı bağlantı testi.
Parametreler şifreli saklanır; yanıtlarda hassas alanlar maskelenir.
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.param_crypto import decrypt_params, encrypt_params, mask_params
from app.models.integration_setting import IntegrationSetting
from app.schemas.integration import IntegrationCreate, IntegrationUpdate, PARAM_SPECS

TCP_TIMEOUT = 5.0
HTTP_TIMEOUT = 8.0


class IntegrationService:
    """Entegrasyon iş mantığı."""

    # ── CRUD ──

    @staticmethod
    def _to_dict(row: IntegrationSetting) -> dict:
        return {
            "id": row.id,
            "integration_type": row.integration_type,
            "name": row.name,
            "enabled": row.enabled,
            "params": mask_params(decrypt_params(row.params_encrypted)),
            "last_test_at": row.last_test_at,
            "last_test_ok": row.last_test_ok,
            "last_test_message": row.last_test_message,
            "notes": row.notes,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    @staticmethod
    def validate_params(integration_type: str, params: dict) -> Optional[str]:
        """Zorunlu parametre kontrolü; hata mesajı veya None döner."""
        missing = [
            spec["label"]
            for spec in PARAM_SPECS.get(integration_type, [])
            if spec.get("required") and not str(params.get(spec["key"], "") or "").strip()
        ]
        if missing:
            return "Zorunlu parametreler eksik: " + ", ".join(missing)
        return None

    @staticmethod
    async def create(db: AsyncSession, data: IntegrationCreate, user_id: str) -> dict:
        row = IntegrationSetting(
            integration_type=data.integration_type,
            name=data.name,
            enabled=data.enabled,
            params_encrypted=encrypt_params(data.params),
            notes=data.notes,
            created_by=user_id,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return IntegrationService._to_dict(row)

    @staticmethod
    async def list(db: AsyncSession, integration_type: Optional[str] = None) -> list[dict]:
        q = select(IntegrationSetting).where(IntegrationSetting.deleted_at.is_(None))
        if integration_type:
            q = q.where(IntegrationSetting.integration_type == integration_type)
        rows = (await db.execute(q.order_by(IntegrationSetting.created_at))).scalars().all()
        return [IntegrationService._to_dict(r) for r in rows]

    @staticmethod
    async def get_row(db: AsyncSession, setting_id: UUID) -> Optional[IntegrationSetting]:
        q = select(IntegrationSetting).where(
            IntegrationSetting.id == setting_id, IntegrationSetting.deleted_at.is_(None)
        )
        return (await db.execute(q)).scalar_one_or_none()

    @staticmethod
    async def update(db: AsyncSession, row: IntegrationSetting, data: IntegrationUpdate, user_id: str) -> dict:
        if data.name is not None:
            row.name = data.name
        if data.enabled is not None:
            row.enabled = data.enabled
        if data.notes is not None:
            row.notes = data.notes
        if data.params is not None:
            current = decrypt_params(row.params_encrypted)
            for k, v in data.params.items():
                # Maskeli değer geri gönderildiyse mevcut gizli değeri koru
                if isinstance(v, str) and v.startswith("••••"):
                    continue
                current[k] = v
            row.params_encrypted = encrypt_params(current)
        row.updated_by = user_id
        await db.commit()
        await db.refresh(row)
        return IntegrationService._to_dict(row)

    @staticmethod
    async def soft_delete(db: AsyncSession, row: IntegrationSetting, user_id: str) -> None:
        row.deleted_at = datetime.now(timezone.utc)
        row.updated_by = user_id
        await db.commit()

    # ── Bağlantı testi ──

    @staticmethod
    async def test_connection(db: AsyncSession, row: IntegrationSetting) -> dict:
        params = decrypt_params(row.params_encrypted)
        err = IntegrationService.validate_params(row.integration_type, params)
        if err:
            ok, message = False, err
        elif row.integration_type == "iot":
            ok, message = await IntegrationService._test_tcp(
                str(params.get("broker_host", "")), int(params.get("broker_port", 0) or 0)
            )
        else:
            ok, message = await IntegrationService._test_http(str(params.get("endpoint_url", "")))

        row.last_test_at = datetime.now(timezone.utc)
        row.last_test_ok = ok
        row.last_test_message = message
        await db.commit()
        return {"ok": ok, "message": message, "tested_at": row.last_test_at}

    @staticmethod
    async def _test_tcp(host: str, port: int) -> tuple[bool, str]:
        """IoT: MQTT broker'a (veya KNX/Hue gateway'e) TCP el sıkışması."""
        if not host or not port:
            return False, "Broker host/port eksik."
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=TCP_TIMEOUT
            )
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return True, f"TCP bağlantısı başarılı: {host}:{port}"
        except (asyncio.TimeoutError, OSError) as e:
            return False, f"TCP bağlantısı kurulamadı ({host}:{port}): {e.__class__.__name__}"

    @staticmethod
    async def _test_http(url: str) -> tuple[bool, str]:
        """HTTP tabanlı entegrasyonlar: endpoint erişilebilirlik kontrolü."""
        if not url:
            return False, "Endpoint URL eksik."
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
                resp = await client.get(url)
            # Kimlik doğrulamasız çağrıda 401/403 de "servis ayakta" demektir
            if resp.status_code < 500:
                return True, f"Servis erişilebilir (HTTP {resp.status_code})."
            return False, f"Servis hata döndürdü (HTTP {resp.status_code})."
        except httpx.HTTPError as e:
            return False, f"Endpoint'e ulaşılamadı: {e.__class__.__name__}"
