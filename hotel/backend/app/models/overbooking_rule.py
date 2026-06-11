from uuid import UUID
from sqlalchemy import String, Float, ForeignKey, Boolean, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class OverbookingRule(BaseModel):
    __tablename__ = "overbooking_rules"

    room_type_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("room_types.id"), nullable=True
    )
    channel_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("channels.id"), nullable=True
    )
    overbooking_percent: Mapped[float] = mapped_column(Float, default=0.0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
