"""E-fatura connector soyut taban sınıfı.

Her e-fatura entegratörü (Foriba, Logo, Uyumsoft, İzibiz) bu arayüzü uygular.
EInvoiceService bu arayüze dayanır; concrete sınıflar sadece HTTP detaylarını
farklılaştırır.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EInvoiceParams:
    """Entegrasyon kaydından çözülmüş e-fatura parametreleri."""
    provider: str = ""
    username: str = ""
    password: str = ""
    endpoint_url: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class SubmitResult:
    """Fatura gönderim sonucu."""
    ok: bool
    invoice_id: str = ""
    error_message: str | None = None
    raw_response: Any = None


@dataclass
class StatusResult:
    """Fatura durum sorgulama sonucu."""
    ok: bool
    status: str = ""
    error_message: str | None = None


@dataclass
class CancelResult:
    """Fatura iptal sonucu."""
    ok: bool
    error_message: str | None = None


class BaseEInvoiceConnector(ABC):
    """Tüm e-fatura connector'ları için sözleşme."""

    code: str = ""
    display_name: str = ""

    def __init__(self, params: EInvoiceParams) -> None:
        self.params = params

    @abstractmethod
    async def submit(self, xml: str) -> SubmitResult:
        """Fatura XML'ini entegratöre gönderir."""
        ...

    @abstractmethod
    async def query_status(self, invoice_id: str) -> StatusResult:
        """GİB tarafındaki fatura durumunu sorgular."""
        ...

    @abstractmethod
    async def cancel(self, invoice_id: str) -> CancelResult:
        """Faturayı iptal eder."""
        ...

    @abstractmethod
    async def test_connection(self) -> SubmitResult:
        """Entegratör bağlantısını test eder."""
        ...


__all__ = [
    "EInvoiceParams",
    "SubmitResult",
    "StatusResult",
    "CancelResult",
    "BaseEInvoiceConnector",
]
