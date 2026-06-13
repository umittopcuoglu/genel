"""Payment Gateway şemaları."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CardDetails(BaseModel):
    """Test/mock kart bilgisi — gerçek entegrasyonda tokenize edilir, asla raw saklanmaz."""
    holder_name: str = Field(min_length=2, max_length=80)
    number: str = Field(min_length=12, max_length=19)
    exp_month: int = Field(ge=1, le=12)
    exp_year: int = Field(ge=2024, le=2099)
    cvc: str = Field(min_length=3, max_length=4)

    @field_validator("number")
    @classmethod
    def _digits(cls, v: str) -> str:
        v = v.replace(" ", "").replace("-", "")
        if not v.isdigit():
            raise ValueError("Kart numarası sadece rakamlardan oluşmalı")
        return v


class ChargeRequest(BaseModel):
    folio_id: Optional[UUID] = None
    reservation_id: Optional[UUID] = None
    amount: Decimal = Field(gt=0)
    currency: Literal["TRY", "EUR", "USD"] = "TRY"
    card: CardDetails
    use_3d_secure: bool = False
    # Belirli bir entegrasyon (provider) hedeflenebilir; verilmezse aktif olan kullanılır
    integration_id: Optional[UUID] = None


class RefundRequest(BaseModel):
    txn_id: UUID
    amount: Optional[Decimal] = Field(default=None, gt=0)
    reason: Optional[str] = Field(default=None, max_length=200)


class PaymentTxnResponse(BaseModel):
    id: UUID
    folio_id: Optional[UUID]
    reservation_id: Optional[UUID]
    provider: str
    kind: str
    status: str
    amount: Decimal
    currency: str
    provider_ref: Optional[str]
    error_message: Optional[str]
    card_last4: Optional[str]
    card_brand: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChargeResponse(BaseModel):
    txn: PaymentTxnResponse
    redirect_url: Optional[str] = None  # 3DS için
    success: bool
