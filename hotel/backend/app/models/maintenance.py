from decimal import Decimal
from datetime import date, datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, JSON, Numeric, Text, Uuid, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.front_office import Room
    from app.models.user import User


class Asset(BaseModel):
    """Equipment/asset inventory."""
    __tablename__ = "assets"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # AC, Plumbing, Electrical
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    warranty_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(15), default="active", nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    maintenance_logs: Mapped[list["MaintenanceLog"]] = relationship("MaintenanceLog", back_populates="asset")


class WorkOrder(BaseModel):
    """Maintenance work orders."""
    __tablename__ = "work_orders"

    room_id: Mapped[str | None] = mapped_column(Uuid, ForeignKey("rooms.id"), nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # Plumbing, Electrical, HVAC
    priority: Mapped[str] = mapped_column(String(15), default="normal", nullable=False)  # low, normal, high, urgent
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    estimated_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    maintenance_logs: Mapped[list["MaintenanceLog"]] = relationship("MaintenanceLog", back_populates="work_order")


class PreventiveMaintenance(BaseModel):
    """Scheduled preventive maintenance."""
    __tablename__ = "preventive_maintenance"

    asset_id: Mapped[str] = mapped_column(Uuid, ForeignKey("assets.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    frequency_days: Mapped[int] = mapped_column(Integer, nullable=False)  # e.g., 90 for quarterly
    last_maintenance_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_maintenance_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(15), default="active", nullable=False)


class MaintenanceLog(BaseModel):
    """Work performed log."""
    __tablename__ = "maintenance_logs"

    work_order_id: Mapped[str] = mapped_column(Uuid, ForeignKey("work_orders.id"), nullable=False)
    asset_id: Mapped[str | None] = mapped_column(Uuid, ForeignKey("assets.id"), nullable=True)
    performed_by: Mapped[str] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    parts_used: Mapped[str | None] = mapped_column(String(200), nullable=True)
    hours_spent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    work_order: Mapped["WorkOrder"] = relationship("WorkOrder", back_populates="maintenance_logs")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="maintenance_logs")
