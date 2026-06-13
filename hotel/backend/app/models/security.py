"""
TASK-017 — Güvenlik & Erişim Kontrol & KVKK modülü modelleri.
Erişim logları, kapı kilitleri, anahtar kartları, güvenlik olayları,
KVKK rıza kayıtları ve veri erişim/silme talepleri.
"""
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Text, Uuid, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class DoorLock(BaseModel):
    """Kapı kilidi envanteri (oda/bölge eşleştirme)."""
    __tablename__ = "door_locks"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    area: Mapped[str] = mapped_column(String(50), nullable=False)  # room, common, restricted
    room_id: Mapped[str | None] = mapped_column(Uuid, ForeignKey("rooms.id"), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(15), default="active", nullable=False)

    access_logs: Mapped[list["AccessLog"]] = relationship("AccessLog", back_populates="door_lock", lazy="selectin")


class KeyCard(BaseModel):
    """Anahtar kartı (misafir/personel)."""
    __tablename__ = "key_cards"

    card_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    owner_type: Mapped[str] = mapped_column(String(15), nullable=False)  # guest, staff
    owner_name: Mapped[str] = mapped_column(String(100), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(15), default="active", nullable=False)  # active, expired, revoked
    reservation_id: Mapped[str | None] = mapped_column(Uuid, ForeignKey("reservations.id"), nullable=True)


class AccessLog(BaseModel):
    """Erişim günlüğü (giriş/çıkış denemeleri)."""
    __tablename__ = "access_logs"

    door_lock_id: Mapped[str | None] = mapped_column(Uuid, ForeignKey("door_locks.id"), nullable=True)
    area: Mapped[str] = mapped_column(String(50), nullable=False)
    card_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    person_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    result: Mapped[str] = mapped_column(String(15), nullable=False)  # granted, denied
    accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    door_lock: Mapped["DoorLock"] = relationship("DoorLock", back_populates="access_logs")


class Incident(BaseModel):
    """Güvenlik olayı."""
    __tablename__ = "incidents"

    title: Mapped[str] = mapped_column(String(150), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(30), nullable=False)  # theft, unauthorized_access, fire, other
    severity: Mapped[str] = mapped_column(String(15), default="low", nullable=False)  # low, medium, high, critical
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(15), default="open", nullable=False)  # open, investigating, resolved, closed
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class KVKKConsent(BaseModel):
    """KVKK misafir rıza kaydı."""
    __tablename__ = "kvkk_consents"

    guest_id: Mapped[str | None] = mapped_column(Uuid, ForeignKey("guests.id"), nullable=True)
    guest_name: Mapped[str] = mapped_column(String(100), nullable=False)
    purpose: Mapped[str] = mapped_column(String(200), nullable=False)  # marketing, data_processing, etc.
    status: Mapped[str] = mapped_column(String(15), default="granted", nullable=False)  # granted, withdrawn
    consent_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DataAccessRequest(BaseModel):
    """KVKK veri erişim/silme talebi."""
    __tablename__ = "data_access_requests"

    guest_id: Mapped[str | None] = mapped_column(Uuid, ForeignKey("guests.id"), nullable=True)
    guest_name: Mapped[str] = mapped_column(String(100), nullable=False)
    request_type: Mapped[str] = mapped_column(String(15), nullable=False)  # access, deletion
    status: Mapped[str] = mapped_column(String(15), default="pending", nullable=False)  # pending, processing, completed, rejected
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
