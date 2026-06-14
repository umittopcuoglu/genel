"""Misafir Wi-Fi Portal servisi: kayıt, doğrulama, senkronizasyon."""
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guest_wifi_session import GuestWiFiSession, GuestWiFiStatus
from app.schemas.guest_wifi import (
    GuestWiFiRegisterRequest,
    GuestWiFiSessionResponse,
    GuestWiFiStatusResponse,
    GuestWiFiSuccessResponse,
)


class GuestWiFiService:
    """Misafir Wi-Fi yönetimi servisi."""

    @staticmethod
    def _generate_wifi_password(length: int = 12) -> str:
        """Güvenli Wi-Fi şifresi üret (harfler + sayılar, özel char yok)."""
        chars = string.ascii_letters + string.digits
        return "".join(secrets.choice(chars) for _ in range(length))

    @staticmethod
    async def register_guest_wifi(
        db: AsyncSession,
        request: GuestWiFiRegisterRequest,
        valid_hours: int = 24,
        ssid: str = "HotelOps-Guest",
    ) -> GuestWiFiSuccessResponse:
        """
        Misafir Wi-Fi kaydı: E-posta + Ad + Koşul Kabul → Geçici şifre.
        Aynı e-posta için son oturum iptal edilir.
        """
        # Aynı e-postanın eski oturumlarını iptal et
        stmt = select(GuestWiFiSession).where(
            (GuestWiFiSession.email == request.email)
            & (GuestWiFiSession.status == GuestWiFiStatus.active)
            & (GuestWiFiSession.deleted_at.is_(None))
        )
        old_sessions = await db.scalars(stmt)
        for session in old_sessions:
            session.status = GuestWiFiStatus.revoked

        # Yeni oturum oluştur
        now = datetime.now()
        valid_until = now + timedelta(hours=valid_hours)

        session = GuestWiFiSession(
            email=request.email,
            guest_name=request.guest_name,
            phone=request.phone,
            wifi_password=GuestWiFiService._generate_wifi_password(),
            ssid=ssid,
            valid_from=now,
            valid_until=valid_until,
            status=GuestWiFiStatus.active,
            terms_accepted=request.terms_accepted,
        )

        db.add(session)
        await db.flush()
        await db.commit()

        return GuestWiFiSuccessResponse(
            ssid=ssid,
            password=session.wifi_password,
            valid_hours=valid_hours,
            valid_until=valid_until,
        )

    @staticmethod
    async def get_wifi_status(
        db: AsyncSession,
        email: str,
    ) -> Optional[GuestWiFiStatusResponse]:
        """E-posta için aktif Wi-Fi oturumunun durumunu döner."""
        stmt = select(GuestWiFiSession).where(
            (GuestWiFiSession.email == email)
            & (GuestWiFiSession.status == GuestWiFiStatus.active)
            & (GuestWiFiSession.deleted_at.is_(None))
        )
        session = await db.scalar(stmt)

        if not session:
            return None

        now = datetime.now()
        remaining = (session.valid_until - now).total_seconds() / 3600  # saat cinsinden

        return GuestWiFiStatusResponse(
            email=session.email,
            status=session.status.value,
            valid_until=session.valid_until,
            remaining_hours=max(0, remaining),
            is_active=(remaining > 0 and session.status == GuestWiFiStatus.active),
        )

    @staticmethod
    async def resend_credentials(
        db: AsyncSession,
        email: str,
    ) -> Optional[GuestWiFiSessionResponse]:
        """Son aktif Wi-Fi oturumunun kimlik bilgilerini tekrar gönder."""
        stmt = select(GuestWiFiSession).where(
            (GuestWiFiSession.email == email)
            & (GuestWiFiSession.status == GuestWiFiStatus.active)
            & (GuestWiFiSession.deleted_at.is_(None))
        ).order_by(GuestWiFiSession.created_at.desc())

        session = await db.scalar(stmt)

        if not session:
            return None

        return GuestWiFiSessionResponse(
            id=str(session.id),
            email=session.email,
            guest_name=session.guest_name,
            wifi_password=session.wifi_password,
            ssid=session.ssid,
            valid_from=session.valid_from,
            valid_until=session.valid_until,
            status=session.status.value,
        )

    @staticmethod
    async def revoke_wifi_session(
        db: AsyncSession,
        email: str,
    ) -> bool:
        """E-posta için tüm aktif Wi-Fi oturumlarını iptal et (superadmin)."""
        stmt = select(GuestWiFiSession).where(
            (GuestWiFiSession.email == email)
            & (GuestWiFiSession.status == GuestWiFiStatus.active)
            & (GuestWiFiSession.deleted_at.is_(None))
        )
        sessions = await db.scalars(stmt)

        found = False
        for session in sessions:
            session.status = GuestWiFiStatus.revoked
            found = True

        if found:
            await db.commit()

        return found
