"""Güvenlik & KVKK servisi.

- AccessLog (kart/PIN/biyometrik kapı erişim olayları)
- KVKK consent yaşam döngüsü (grant/revoke)
- KVKK Data Subject Requests (access/erase/rectify/portability)
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.front_office import Guest
from app.models.security import AccessLog, DataSubjectRequest, KVKKConsent


class SecurityService:
    @staticmethod
    async def log_access(
        db: AsyncSession,
        door_code: str,
        method: str = "card",
        granted: bool = True,
        user_id: Optional[UUID] = None,
        guest_id: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> AccessLog:
        log = AccessLog(
            door_code=door_code,
            method=method,
            granted=granted,
            user_id=user_id,
            guest_id=guest_id,
            reason=reason,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    # ── KVKK Consent ──

    @staticmethod
    async def grant_consent(
        db: AsyncSession,
        guest_id: UUID,
        purpose: str,
        text_version: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> KVKKConsent:
        guest = await db.get(Guest, guest_id)
        if guest is None:
            raise ValueError("Misafir bulunamadı")
        # Aynı amaç için aktif consent varsa eskisini revoke etmeden yeni kayıt aç
        existing_q = await db.execute(
            select(KVKKConsent).where(
                KVKKConsent.guest_id == guest_id,
                KVKKConsent.purpose == purpose,
                KVKKConsent.revoked_at.is_(None),
                KVKKConsent.granted.is_(True),
                KVKKConsent.deleted_at.is_(None),
            )
        )
        active = existing_q.scalars().first()
        if active:
            return active

        c = KVKKConsent(
            guest_id=guest_id,
            purpose=purpose,
            granted=True,
            text_version=text_version,
            ip_address=ip_address,
        )
        db.add(c)
        await db.commit()
        await db.refresh(c)
        return c

    @staticmethod
    async def revoke_consent(db: AsyncSession, consent_id: UUID) -> KVKKConsent:
        c = await db.get(KVKKConsent, consent_id)
        if c is None:
            raise ValueError("Onay kaydı bulunamadı")
        if c.revoked_at is not None:
            raise ValueError("Bu onay zaten geri çekilmiş")
        c.granted = False
        c.revoked_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(c)
        return c

    # ── Data Subject Requests ──

    @staticmethod
    async def open_request(
        db: AsyncSession, guest_id: UUID, request_type: str, notes: Optional[str] = None
    ) -> DataSubjectRequest:
        if request_type not in ("access", "erase", "rectify", "portability"):
            raise ValueError("Geçersiz talep türü")
        guest = await db.get(Guest, guest_id)
        if guest is None:
            raise ValueError("Misafir bulunamadı")
        req = DataSubjectRequest(guest_id=guest_id, request_type=request_type, notes=notes)
        db.add(req)
        await db.commit()
        await db.refresh(req)
        return req

    @staticmethod
    async def fulfill_request(db: AsyncSession, request_id: UUID) -> DataSubjectRequest:
        req = await db.get(DataSubjectRequest, request_id)
        if req is None:
            raise ValueError("Talep bulunamadı")
        if req.status != "pending":
            raise ValueError("Sadece bekleyen talep tamamlanabilir")
        guest = await db.get(Guest, req.guest_id)
        if guest is None:
            raise ValueError("Misafir bulunamadı")

        if req.request_type == "access":
            req.response_payload = {
                "id": str(guest.id),
                "first_name": guest.first_name,
                "last_name": guest.last_name,
                "email": guest.email,
                "phone": guest.phone,
                "is_vip": guest.is_vip,
            }
        elif req.request_type == "erase":
            # Pseudonymize: kişiselleştirilemeyecek hale getir
            guest.first_name = "ANON"
            guest.last_name = "ANON"
            guest.email = None
            guest.phone = None
            req.response_payload = {"anonymized": True}
        elif req.request_type == "portability":
            req.response_payload = {
                "format": "json",
                "exported": {
                    "first_name": guest.first_name,
                    "last_name": guest.last_name,
                    "email": guest.email,
                },
            }
        # rectify için müşteri talep notunda hangi alanın değişeceği belirtilir;
        # operatör manuel düzenler ve fulfill ile durumu kapatır
        req.status = "completed"
        req.completed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(req)
        return req
