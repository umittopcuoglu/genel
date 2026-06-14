"""Misafir Wi-Fi Portal: Herkese açık endpoint'ler."""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.rbac import require_roles
from app.schemas.guest_wifi import (
    GuestWiFiRegisterRequest,
    GuestWiFiStatusResponse,
    GuestWiFiSessionResponse,
    GuestWiFiSuccessResponse,
)
from app.services.guest_wifi_service import GuestWiFiService

router = APIRouter(prefix="/api/v1/guest-wifi", tags=["guest-wifi"])


@router.post("/register", response_model=GuestWiFiSuccessResponse)
async def register_guest_wifi(
    request: GuestWiFiRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> GuestWiFiSuccessResponse:
    """
    Misafir Wi-Fi kaydı (herkese açık).
    E-posta, Ad, Koşul Kabul → 24 saatlik geçici şifre.
    """
    if not request.terms_accepted:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Koşul ve Gizlilik Politikası'nı kabul etmelisiniz.",
        )

    return await GuestWiFiService.register_guest_wifi(
        db=db,
        request=request,
        valid_hours=24,
        ssid="HotelOps-Guest",
    )


@router.get("/status/{email}", response_model=GuestWiFiStatusResponse)
async def get_wifi_status(
    email: str,
    db: AsyncSession = Depends(get_db),
) -> GuestWiFiStatusResponse:
    """Wi-Fi oturumunun durumunu kontrol et (herkese açık, E-posta giriş)."""
    status_resp = await GuestWiFiService.get_wifi_status(db=db, email=email)

    if not status_resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu e-posta için aktif Wi-Fi oturumu bulunamadı.",
        )

    return status_resp


@router.post("/resend-credentials/{email}", response_model=GuestWiFiSessionResponse)
async def resend_credentials(
    email: str,
    db: AsyncSession = Depends(get_db),
) -> GuestWiFiSessionResponse:
    """Kimlik bilgilerini tekrar gönder (herkese açık, E-posta doğrulama)."""
    session_resp = await GuestWiFiService.resend_credentials(db=db, email=email)

    if not session_resp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu e-posta için kayıtlı Wi-Fi oturumu bulunamadı.",
        )

    return session_resp


@router.delete("/revoke/{email}")
async def revoke_wifi_session(
    email: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_roles(["superadmin"])),
) -> dict:
    """Wi-Fi erişimini iptal et (superadmin only)."""
    found = await GuestWiFiService.revoke_wifi_session(db=db, email=email)

    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu e-posta için aktif Wi-Fi oturumu bulunamadı.",
        )

    return {"success": True, "message": f"Wi-Fi erişimi iptal edildi: {email}"}
