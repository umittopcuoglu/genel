from uuid import UUID
from sqlalchemy import String, Float, ForeignKey, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class ChannelMapping(BaseModel):
    __tablename__ = "channel_mappings"

    channel_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("channels.id"), nullable=False)
    room_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("rooms.id"), nullable=False)
    external_room_id: Mapped[str] = mapped_column(String(255), nullable=False)
    mapping_status: Mapped[str] = mapped_column(String(50), default="active")
    auto_match_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
