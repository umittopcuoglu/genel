"""
Misafir Wi-Fi Portal: kayıt, oturum yönetimi.
İnternet erişim için geçici şifre ve SSID sağlar.
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.models.base import BaseModel


class GuestWiFiStatus(str, enum.Enum):
    """Wi-Fi erişim durumu."""
    active = "active"
    expired = "expired"
    revoked = "revoked"


class GuestWiFiSession(BaseModel):
    """Misafir Wi-Fi oturumu: E-posta, geçici şifre, geçerlilik süresi."""
    __tablename__ = "guest_wifi_sessions"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=False, index=True)
    guest_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    wifi_password: Mapped[str] = mapped_column(String(255), nullable=False)
    ssid: Mapped[str] = mapped_column(String(255), nullable=False, default="HotelOps-Guest")

    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)  # Format: AA:BB:CC:DD:EE:FF

    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now
    )
    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    status: Mapped[GuestWiFiStatus] = mapped_column(
        Enum(GuestWiFiStatus),
        default=GuestWiFiStatus.active,
        nullable=False
    )

    terms_accepted: Mapped[bool] = mapped_column(Boolean, default=False)

    class Config:
        from_attributes = True
