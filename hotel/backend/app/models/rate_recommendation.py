from uuid import UUID
from decimal import Decimal
from sqlalchemy import String, Numeric, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class RateRecommendation(BaseModel):
    __tablename__ = "rate_recommendations"

    room_type_id: Mapped[UUID] = mapped_column(ForeignKey("room_types.id"))
    date: Mapped[str] = mapped_column(String(10))
    recommended_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    current_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    price_change_percent: Mapped[float] = mapped_column(Float)
    rationale: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Float)
    historical_avg_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    occupancy_forecast: Mapped[float] = mapped_column(Float)
    demand_trend: Mapped[str] = mapped_column(String(50))
    competitor_avg_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="suggested")
