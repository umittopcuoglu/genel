"""
Çok-Mülk Yönetimi modelleri: Otel zinciri, mülkler, konsolide raporlar.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, JSON, Numeric, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Chain(BaseModel):
    """Otel zinciri."""
    __tablename__ = "chains"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Chain {self.code}: {self.name}>"


class Property(BaseModel):
    """Otel/mülk (zincire bağlı)."""
    __tablename__ = "properties"

    chain_id: Mapped[str] = mapped_column(ForeignKey("chains.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    property_type: Mapped[str] = mapped_column(
        String(30), default="hotel", nullable=False
    )  # hotel, resort, hostel, villa, apartment
    address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="TRY", nullable=False)
    timezone: Mapped[str] = mapped_column(String(30), default="Europe/Istanbul", nullable=False)
    star_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    total_rooms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Property {self.code}: {self.name}>"


class PropertySyncLog(BaseModel):
    """Mülkler arası senkronizasyon logu."""
    __tablename__ = "property_sync_logs"

    property_id: Mapped[str] = mapped_column(ForeignKey("properties.id"), nullable=False)
    sync_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # rate_push, availability_push, reservation_pull, guest_data, financial
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success, failed, in_progress
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<PropertySyncLog {self.sync_type}: {self.status}>"


class ConsolidatedReport(BaseModel):
    """Konsolide rapor (zincir geneli KPI)."""
    __tablename__ = "consolidated_reports"

    chain_id: Mapped[str] = mapped_column(ForeignKey("chains.id"), nullable=False)
    report_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # daily, weekly, monthly, quarterly, yearly
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    total_occupancy: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"), nullable=False)
    total_rooms_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_available_rooms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_daily_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"), nullable=False)
    revpar: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"), nullable=False)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<ConsolidatedReport {self.report_type} {self.report_date}>"


class PropertyUser(BaseModel):
    """Mülk bazında kullanıcı yetkilendirmesi."""
    __tablename__ = "property_users"

    property_id: Mapped[str] = mapped_column(ForeignKey("properties.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    role: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # property_admin, property_manager, property_frontdesk, property_housekeeping
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<PropertyUser User {self.user_id} @ Property {self.property_id}>"
