"""
Reservasyon modulu ek modelleri: rate_plans ve availability.
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String, Integer, Numeric as SA_Decimal, Boolean, Date,
    ForeignKey, UniqueConstraint, Index, Uuid
)
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

# Dialect-bağımsız JSON: Postgres'te JSONB, SQLite testlerinde JSON
JSON_VARIANT = JSON().with_variant(JSONB, "postgresql")


class RatePlan(BaseModel):
    __tablename__ = "rate_plans"

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    room_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("room_types.id"), nullable=False, index=True
    )
    base_rate: Mapped[Decimal] = mapped_column(SA_Decimal(10, 2), nullable=False, default=0)
    restrictions: Mapped[Optional[dict]] = mapped_column(JSON_VARIANT, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    room_type: Mapped["RoomType"] = relationship()  # noqa: F821

    def __repr__(self):
        return f"<RatePlan {self.code}: {self.base_rate}>"


class Availability(BaseModel):
    __tablename__ = "availability"

    room_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("room_types.id"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    available_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sold_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    room_type: Mapped["RoomType"] = relationship()  # noqa: F821

    __table_args__ = (
        UniqueConstraint("room_type_id", "date", name="uq_avail_roomtype_date"),
        Index("ix_availability_roomtype_date", "room_type_id", "date"),
    )

    def __repr__(self):
        return f"<Availability {self.room_type_id} @ {self.date}: {self.sold_count}/{self.available_count}>"
