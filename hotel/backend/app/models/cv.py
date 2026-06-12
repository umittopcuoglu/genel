"""
Computer Vision modelleri: Oda kalite kontrol, envanter yönetimi.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, JSON, Numeric, Boolean, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CVModel(BaseModel):
    """Eğitilmiş CV modeli kaydı."""
    __tablename__ = "cv_models"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    model_type: Mapped[str] = mapped_column(String(30), nullable=False)  # inspection, object_detection, defect_classification
    framework: Mapped[str] = mapped_column(String(30), nullable=False)  # yolov8, tensorflow, pytorch
    accuracy: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    model_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CVModel {self.name} v{self.version}>"


class RoomInspection(BaseModel):
    """Oda kalite kontrol denetimi."""
    __tablename__ = "room_inspections"

    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    inspector_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    cv_model_id: Mapped[Optional[str]] = mapped_column(ForeignKey("cv_models.id"), nullable=True)
    inspection_type: Mapped[str] = mapped_column(
        String(30), default="daily", nullable=False
    )  # daily, deep_clean, pre_arrival, post_departure, preventive
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, in_progress, completed, failed
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 0-100
    defects_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    raw_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<RoomInspection Room {self.room_id} ({self.status})>"


class InspectionDefect(BaseModel):
    """Denetimde tespit edilen kusur."""
    __tablename__ = "inspection_defects"

    inspection_id: Mapped[str] = mapped_column(ForeignKey("room_inspections.id"), nullable=False)
    defect_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # dirty_carpet, broken_lamp, stained_bedding, leaky_faucet, missing_towel, etc.
    category: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # cleanliness, maintenance, amenity, furniture, safety
    severity: Mapped[str] = mapped_column(
        String(10), default="minor", nullable=False
    )  # critical, major, minor, cosmetic
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)  # AI confidence 0-100%
    position: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"x": 100, "y": 200, "w": 50, "h": 50}
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    suggested_action: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    work_order_id: Mapped[Optional[str]] = mapped_column(ForeignKey("work_orders.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<InspectionDefect {self.defect_type} ({self.severity})>"


class InventorySnapshot(BaseModel):
    """Oda envanter anlık görüntüsü (CV ile tespit edilen eşyalar)."""
    __tablename__ = "inventory_snapshots"

    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    inspection_id: Mapped[Optional[str]] = mapped_column(ForeignKey("room_inspections.id"), nullable=True)
    item_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # towel, pillow, blanket, hanger, glass, remote, lamp, etc.
    expected_count: Mapped[int] = mapped_column(Integer, nullable=False)
    detected_count: Mapped[int] = mapped_column(Integer, nullable=False)
    missing_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    snapshot_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<InventorySnapshot {self.item_type}: {self.detected_count}/{self.expected_count}>"
