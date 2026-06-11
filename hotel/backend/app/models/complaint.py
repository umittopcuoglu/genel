from uuid import UUID
from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class Complaint(BaseModel):
    __tablename__ = "complaints"

    guest_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("guests.id"))
    reservation_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("reservations.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    complaint_type: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="open")
    assigned_to: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
