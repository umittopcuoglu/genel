"""Misafir Wi-Fi Portal: request/response şemaları."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class GuestWiFiRegisterRequest(BaseModel):
    """Wi-Fi kayıt isteği."""
    email: EmailStr
    guest_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    terms_accepted: bool = Field(..., description="Koşul ve Gizlilik Politikası'nı kabul et")


class GuestWiFiSessionResponse(BaseModel):
    """Wi-Fi oturumu yanıtı."""
    id: str
    email: str
    guest_name: str
    wifi_password: str
    ssid: str
    valid_from: datetime
    valid_until: datetime
    status: str

    class Config:
        from_attributes = True


class GuestWiFiStatusResponse(BaseModel):
    """Wi-Fi durumu yanıtı."""
    email: str
    status: str
    valid_until: datetime
    remaining_hours: float = Field(..., description="Kalan saat sayısı")
    is_active: bool


class GuestWiFiSuccessResponse(BaseModel):
    """Başarılı kayıt yanıtı."""
    success: bool = True
    message: str = "Wi-Fi kaydı başarılı"
    ssid: str
    password: str
    valid_hours: int
    valid_until: datetime
