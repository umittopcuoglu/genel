from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class Channel(BaseModel):
    __tablename__ = "channels"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False)
    credentials_encrypted: Mapped[str] = mapped_column(String(1000), nullable=False)
    api_base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sync_interval_hours: Mapped[int] = mapped_column(Integer, default=4)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rate_limit_requests: Mapped[int] = mapped_column(Integer, default=100)
    rate_limit_window_seconds: Mapped[int] = mapped_column(Integer, default=60)
