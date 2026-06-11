from uuid import UUID
from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class Feedback(BaseModel):
    __tablename__ = "feedback"

    guest_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("guests.id"))
    reservation_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("reservations.id"))
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text)
    categories: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50), default="new")
    manager_response: Mapped[str | None] = mapped_column(Text, nullable=True)
