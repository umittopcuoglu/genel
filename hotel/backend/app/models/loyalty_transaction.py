from uuid import UUID
from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel, GUIDString


class LoyaltyTransaction(BaseModel):
    __tablename__ = "loyalty_transactions"

    loyalty_account_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("loyalty_accounts.id"))
    transaction_type: Mapped[str] = mapped_column(String(50))
    amount: Mapped[int] = mapped_column(Integer)
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_id: Mapped[UUID | None] = mapped_column(GUIDString(), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    balance_before: Mapped[int] = mapped_column(Integer)
    balance_after: Mapped[int] = mapped_column(Integer)
