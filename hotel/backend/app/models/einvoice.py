from uuid import UUID
from decimal import Decimal
from sqlalchemy import String, Numeric, Text, LargeBinary, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class EInvoice(BaseModel):
    __tablename__ = "einvoices"

    invoice_number: Mapped[str] = mapped_column(String(50), unique=True)
    invoice_date: Mapped[str] = mapped_column(String(10))
    customer_name: Mapped[str] = mapped_column(String(255))
    customer_tax_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    customer_email: Mapped[str] = mapped_column(String(255))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    kdv_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    e_invoice_uuid: Mapped[str | None] = mapped_column(String(36), nullable=True)
    einvoice_status: Mapped[str] = mapped_column(String(50), default="draft")
    xml_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    xml_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pdf_content: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    gib_response_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gib_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_folio_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("folios.id"), nullable=True)
