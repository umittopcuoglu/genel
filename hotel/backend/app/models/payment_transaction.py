"""Payment Gateway işlem kayıtları (charge / refund).

`Payment` modeli folio'ya bağlı muhasebe kaydı; bu model ise gateway tarafındaki
charge/refund/3DS yaşam döngüsünü tutar. Aynı folio_id üzerinde N tane gateway
denemesi olabilir (başarısız 3DS, retry, refund vb.).
"""
import enum
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, ForeignKey, Uuid, Index, Text
from sqlalchemy.types import Numeric as SA_Decimal
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class PaymentTxnStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentTxnKind(str, enum.Enum):
    CHARGE = "charge"
    REFUND = "refund"


class PaymentTransaction(BaseModel):
    __tablename__ = "payment_transactions"

    folio_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("folios.id"), nullable=True, index=True
    )
    reservation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("reservations.id"), nullable=True, index=True
    )
    integration_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("integration_settings.id"), nullable=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(10), nullable=False, default=PaymentTxnKind.CHARGE.value)
    status: Mapped[str] = mapped_column(String(15), nullable=False, default=PaymentTxnStatus.PENDING.value, index=True)
    amount: Mapped[Decimal] = mapped_column(SA_Decimal(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    # Gateway tarafı referansı
    provider_ref: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    # 3D Secure callback / iade için orijinal işlem
    parent_txn_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("payment_transactions.id"), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Sadeleştirilmiş kart bilgisi (PCI: tam pan asla saklanmaz — sadece son 4)
    card_last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    card_brand: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    __table_args__ = (
        Index("ix_payment_txn_provider_ref", "provider", "provider_ref"),
    )
