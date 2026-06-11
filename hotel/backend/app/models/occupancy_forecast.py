from uuid import UUID
from sqlalchemy import String, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class OccupancyForecast(BaseModel):
    __tablename__ = "occupancy_forecasts"

    room_type_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("room_types.id"), nullable=True
    )
    forecast_date: Mapped[str] = mapped_column(String(10))
    predicted_occupancy_percent: Mapped[float] = mapped_column(Float)
    predicted_rooms_occupied: Mapped[int] = mapped_column(Integer)
    confidence_interval: Mapped[str] = mapped_column(String(100))
    forecast_method: Mapped[str] = mapped_column(String(100))
    forecast_horizon_days: Mapped[int] = mapped_column(Integer)
    actual_occupancy_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    forecast_error_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
