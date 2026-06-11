from uuid import UUID
from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"

    chat_session_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("chat_sessions.id"))
    role: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    sentiment: Mapped[str | None] = mapped_column(String(50), nullable=True)
