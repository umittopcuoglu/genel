"""
Finans modelleri: folio, folio_items, payments, night_audit_runs.
Muhasebe & Cashiering modülü (TASK-004).
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String, Integer, Numeric as SA_Decimal, Date, DateTime,
    Text, ForeignKey, Enum as SA_Enum, UniqueConstraint, Index,
    Uuid
)
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

# Dialect-bağımsız JSON: Postgres'te JSONB, SQLite testlerinde JSON
JSON_VARIANT = JSON().with_variant(JSONB, "postgresql")
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import BaseModel


class FolioStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class FolioItemType(str, enum.Enum):
    ROOM = "room"
    FNB = "fnb"
    EXTRA = "extra"
    TAX = "tax"
    ADJ = "adj"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    VPOS = "vpos"


class PaymentStatus(str, enum.Enum):
    COMPLETED = "completed"
    REFUNDED = "refunded"
    FAILED = "failed"


class Folio(BaseModel):
    __tablename__ = "folios"

    reservation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reservations.id"), nullable=False, index=True
    )
    guest_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("guests.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default=FolioStatus.OPEN.value, index=True
    )
    total: Mapped[Decimal] = mapped_column(SA_Decimal(12, 2), nullable=False, default=0)
    balance: Mapped[Decimal] = mapped_column(SA_Decimal(12, 2), nullable=False, default=0)
    # Faz 2 raporlama (dashboard ADR/RevPAR): folio kapanış tarihi
    closed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)

    items: Mapped[list["FolioItem"]] = relationship(
        "FolioItem", back_populates="folio", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="folio", cascade="all, delete-orphan"
    )

    def recalculate(self):
        self.total = sum(item.total for item in (self.items or []))
        paid = sum(p.amount for p in (self.payments or []) if p.status == PaymentStatus.COMPLETED.value)
        refunded = sum(p.amount for p in (self.payments or []) if p.status == PaymentStatus.REFUNDED.value)
        self.balance = self.total - paid + refunded

    def __repr__(self):
        return f"<Folio {self.id}: total={self.total} balance={self.balance}>"


class FolioItem(BaseModel):
    __tablename__ = "folio_items"

    folio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("folios.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(SA_Decimal(10, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(SA_Decimal(5, 2), nullable=False, default=18)
    total: Mapped[Decimal] = mapped_column(SA_Decimal(12, 2), nullable=False, default=0)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    folio: Mapped["Folio"] = relationship("Folio", back_populates="items")

    def calculate_total(self) -> Decimal:
        return Decimal(str(self.qty)) * self.unit_price * (1 + self.tax_rate / Decimal("100"))

    __table_args__ = (
        Index("ix_folio_items_folio_type", "folio_id", "type"),
    )


class Payment(BaseModel):
    __tablename__ = "payments"

    folio_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("folios.id"), nullable=False, index=True
    )
    method: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(SA_Decimal(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=PaymentStatus.COMPLETED.value)

    folio: Mapped["Folio"] = relationship("Folio", back_populates="payments")

    __table_args__ = (
        Index("ix_payments_folio_method", "folio_id", "method"),
    )


class NightAuditRun(BaseModel):
    __tablename__ = "night_audit_runs"

    business_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    run_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )
    stats: Mapped[Optional[dict]] = mapped_column(JSON_VARIANT, nullable=True)

    def __repr__(self):
        return f"<NightAuditRun {self.business_date}>"
