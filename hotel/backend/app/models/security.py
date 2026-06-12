"""Güvenlik & KVKK modelleri: AccessControl, KVKKConsent, DataExportRequest, DataDeletionRequest."""
import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Uuid, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AccessLog(BaseModel):
    """Kart/şifre/biyometrik kapı erişim olayları."""
    __tablename__ = "security_access_logs"

    door_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    guest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("guests.id"), nullable=True
    )
    method: Mapped[str] = mapped_column(String(30), nullable=False, default="card")  # card/pin/biometric/nfc
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)


class KVKKConsent(BaseModel):
    """KVKK aydınlatma metni onayları."""
    __tablename__ = "kvkk_consents"

    guest_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("guests.id"), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(60), nullable=False)  # marketing/operational/legal
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    text_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)


class DataSubjectRequest(BaseModel):
    """KVKK 11. madde hakları: erişim, düzeltme, silinme, taşınabilirlik."""
    __tablename__ = "kvkk_data_requests"

    guest_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("guests.id"), nullable=False, index=True)
    request_type: Mapped[str] = mapped_column(String(20), nullable=False)  # access/erase/rectify/portability
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending/completed/rejected
    response_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
