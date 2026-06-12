"""
GDS Integration modelleri (TASK-019): Amadeus / Sabre / Travelport.
GDSChannel, GDSReservation, GDSRateMapping, GDSSyncLog.
Şema/migration: schemas/gds.py + migrations/versions/015_add_gds.py ile birebir.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, JSON, Numeric, Boolean, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class GDSChannel(BaseModel):
    """GDS sağlayıcı bağlantısı (Amadeus, Sabre, Travelport)."""
    __tablename__ = "gds_channels"

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # amadeus, sabre, travelport
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # kimlik/endpoint (şifreli) — mock-first
    supported_actions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"ari_push": true, "res_pull": true}
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<GDSChannel {self.code} ({self.provider})>"


class GDSReservation(BaseModel):
    """GDS'ten çekilen ve otele senkronize edilen rezervasyon."""
    __tablename__ = "gds_reservations"

    channel_id: Mapped[str] = mapped_column(Uuid, ForeignKey("gds_channels.id"), nullable=False, index=True)
    gds_reservation_id: Mapped[str] = mapped_column(String(100), nullable=False)
    hotel_reservation_id: Mapped[Optional[str]] = mapped_column(Uuid, ForeignKey("reservations.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)  # pending, synced, failed, cancelled
    guest_name: Mapped[str] = mapped_column(String(100), nullable=False)
    guest_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    adults: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    children: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    room_type_code: Mapped[str] = mapped_column(String(20), nullable=False)
    rate_plan_code: Mapped[str] = mapped_column(String(20), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="TRY", nullable=False)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    sync_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<GDSReservation {self.gds_reservation_id} status={self.status}>"


class GDSRateMapping(BaseModel):
    """GDS oda tipi/oran kodu ↔ otel oda tipi/rate plan eşleştirmesi."""
    __tablename__ = "gds_rate_mappings"

    channel_id: Mapped[str] = mapped_column(Uuid, ForeignKey("gds_channels.id"), nullable=False, index=True)
    gds_room_type_code: Mapped[str] = mapped_column(String(30), nullable=False)
    gds_rate_plan_code: Mapped[str] = mapped_column(String(30), nullable=False)
    hotel_room_type_id: Mapped[str] = mapped_column(Uuid, ForeignKey("room_types.id"), nullable=False)
    hotel_rate_plan_id: Mapped[Optional[str]] = mapped_column(Uuid, ForeignKey("rate_plans.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    markup_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<GDSRateMapping {self.gds_room_type_code}/{self.gds_rate_plan_code}>"


class GDSSyncLog(BaseModel):
    """GDS senkronizasyon geçmişi (ARI push / rez pull)."""
    __tablename__ = "gds_sync_logs"

    channel_id: Mapped[str] = mapped_column(Uuid, ForeignKey("gds_channels.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # ari_push, res_pull, rate_update
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # success, failed, partial
    request_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    response_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    performed_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    def __repr__(self) -> str:
        return f"<GDSSyncLog {self.action} status={self.status}>"
