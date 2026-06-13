from __future__ import annotations

import logging
from decimal import Decimal
from uuid import uuid4

from . import BasePaymentConnector, CardInfo, ChargeResult, PaymentParams, RefundResult

logger = logging.getLogger(__name__)


class IyzicoConnector(BasePaymentConnector):
    code = "iyzico"
    display_name = "iyzico"

    def __init__(self, params: PaymentParams) -> None:
        super().__init__(params)

    @property
    def _is_live(self) -> bool:
        return bool(self.params.endpoint_url)

    async def charge(
        self, amount: Decimal, currency: str, card: CardInfo
    ) -> ChargeResult:
        if self._is_live:
            logger.info(
                "iyzico live charge: %s %s -> %s (mock fallback)",
                amount, currency, self.params.endpoint_url,
            )
        return ChargeResult(
            ok=True,
            provider_ref=f"MOCK-IYZICO-{uuid4().hex[:12]}",
        )

    async def refund(
        self, provider_ref: str, amount: Decimal, currency: str
    ) -> RefundResult:
        if self._is_live:
            logger.info(
                "iyzico live refund: %s %s ref=%s (mock fallback)",
                amount, currency, provider_ref,
            )
        return RefundResult(
            ok=True,
            provider_ref=f"MOCK-IYZICO-REF-{uuid4().hex[:12]}",
        )

    async def test_connection(self) -> ChargeResult:
        if self._is_live:
            logger.info("iyzico test_connection -> %s (mock fallback)", self.params.endpoint_url)
        return ChargeResult(ok=True, provider_ref="MOCK-IYZICO-TEST")
