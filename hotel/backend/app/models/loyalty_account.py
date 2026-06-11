from uuid import UUID
from decimal import Decimal
from sqlalchemy import ForeignKey, Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class LoyaltyAccount(BaseModel):
    __tablename__ = "loyalty_accounts"

    guest_id: Mapped[UUID] = mapped_column(ForeignKey("guests.id"))
    tier: Mapped[str] = mapped_column(String(50), default="bronze")
    tier_since: Mapped[str] = mapped_column(String(10))
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    available_points: Mapped[int] = mapped_column(Integer, default=0)
    lifetime_stays: Mapped[int] = mapped_column(Integer, default=0)
    lifetime_revenue: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal(0))
    status: Mapped[str] = mapped_column(String(50), default="active")
    suspension_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
