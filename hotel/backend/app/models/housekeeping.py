"""
Housekeeping modelleri: tasks, lost_found, minibar_items.
TASK-005: Modül 5 - Housekeeping.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String, Integer, Decimal as SA_Decimal, DateTime,
    Text, ForeignKey, Enum as SA_Enum, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# ──── Housekeeping Tasks ────

class HousekeepingTask(BaseModel):
    __tablename__ = "housekeeping_tasks"

    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rooms.id"), nullable=False, index=True
    )
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    type: Mapped[str] = mapped_column(
        String(15), nullable=False, default="stayover"
    )
    status: Mapped[str] = mapped_column(
        String(15), nullable=False, default="pending", index=True
    )
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    room = relationship("Room", lazy="joined")
    assignee = relationship("User", lazy="joined")

    __table_args__ = (
        Index("ix_housekeeping_room_status", "room_id", "status"),
        Index("ix_housekeeping_assigned", "assigned_to", "status"),
    )


# ──── Lost & Found ────

class LostFound(BaseModel):
    __tablename__ = "lost_found"

    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rooms.id"), nullable=False, index=True
    )
    found_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    item_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(15), nullable=False, default="stored", index=True
    )
    returned_to: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    returned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    room = relationship("Room", lazy="joined")
    finder = relationship("User", lazy="joined")

    __table_args__ = (
        Index("ix_lost_found_room_status", "room_id", "status"),
    )


# ──── Minibar Items ────

class MinibarItem(BaseModel):
    __tablename__ = "minibar_items"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[Decimal] = mapped_column(SA_Decimal(10, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(
        SA_Decimal(5, 2), nullable=False, default=18
    )
