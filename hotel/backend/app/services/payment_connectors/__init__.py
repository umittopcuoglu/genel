"""Payment connector soyut taban sınıfı.

Her ödeme sağlayıcı (iyzico, Stripe, PayTR, Craftgate) bu arayüzü uygular.
PaymentService bu arayüze dayanır; concrete sınıflar sadece HTTP detaylarını farklılaştırır.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class PaymentParams:
    """Entegrasyon kaydından çözülmüş ödeme parametreleri."""
    provider: str = ""
    api_key: str = ""
    secret_key: str = ""
    merchant_id: str = ""
    endpoint_url: str = ""
    use_3d_secure: bool = False
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class CardInfo:
    number: str
    holder_name: str
    expire_month: str
    expire_year: str
    cvc: str


@dataclass
class ChargeResult:
    ok: bool
    provider_ref: str = ""
    error_code: str | None = None
    error_message: str | None = None
    requires_3ds: bool = False
    redirect_url: str | None = None
    raw_response: Any = None


@dataclass
class RefundResult:
    ok: bool
    provider_ref: str = ""
    error_message: str | None = None
    raw_response: Any = None


class BasePaymentConnector(ABC):
    """Tüm ödeme connector'ları için sözleşme."""

    code: str = ""
    display_name: str = ""

    def __init__(self, params: PaymentParams) -> None:
        self.params = params

    @abstractmethod
    async def charge(
        self, amount: Decimal, currency: str, card: CardInfo
    ) -> ChargeResult: ...

    @abstractmethod
    async def refund(
        self, provider_ref: str, amount: Decimal, currency: str
    ) -> RefundResult: ...

    @abstractmethod
    async def test_connection(self) -> ChargeResult: ...
