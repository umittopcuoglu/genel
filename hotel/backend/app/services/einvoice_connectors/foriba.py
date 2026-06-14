"""Foriba (GİB Portal) e-fatura connector'ı — mock implementasyon."""
from __future__ import annotations

from uuid import uuid4

from app.services.einvoice_connectors import (
    BaseEInvoiceConnector,
    CancelResult,
    StatusResult,
    SubmitResult,
)


class ForibaConnector(BaseEInvoiceConnector):
    code = "foriba"
    display_name = "Foriba"

    async def submit(self, xml: str) -> SubmitResult:
        invoice_id = str(uuid4())
        return SubmitResult(
            ok=True,
            invoice_id=invoice_id,
            raw_response={"mock": True, "provider": self.code},
        )

    async def query_status(self, invoice_id: str) -> StatusResult:
        return StatusResult(ok=True, status="delivered")

    async def cancel(self, invoice_id: str) -> CancelResult:
        return CancelResult(ok=True)

    async def test_connection(self) -> SubmitResult:
        return SubmitResult(
            ok=True,
            invoice_id="",
            raw_response={"mock": True, "ping": "pong"},
        )
