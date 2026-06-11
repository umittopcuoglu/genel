from uuid import UUID
from sqlalchemy import ForeignKey, String, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class ChatSession(BaseModel):
    __tablename__ = "chat_sessions"

    guest_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("guests.id"))
    status: Mapped[str] = mapped_column(String(50), default="active")
    context: Mapped[dict] = mapped_column(JSON, default={})
