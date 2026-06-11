from uuid import UUID
from decimal import Decimal
from sqlalchemy import String, Numeric, ForeignKey, Text, DATETIME, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel, GUIDString


class LedgerEntry(BaseModel):
    __tablename__ = "ledger_entries"

    journal_name: Mapped[str] = mapped_column(String(100))
    entry_date: Mapped[str] = mapped_column(String(10))
    entry_number: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str] = mapped_column(Text)
    debit_account_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("chart_of_accounts.id"))
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    credit_account_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("chart_of_accounts.id"))
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_id: Mapped[UUID | None] = mapped_column(GUIDString(), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    posted_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    posted_at: Mapped[str | None] = mapped_column(DATETIME, nullable=True)
