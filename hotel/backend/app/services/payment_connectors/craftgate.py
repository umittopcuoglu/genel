from __future__ import annotations

import logging
from decimal import Decimal
from uuid import uuid4

from . import BasePaymentConnector, CardInfo, ChargeResult, PaymentParams, RefundResult

logger = logging.getLogger(__name__)


class CraftgateConnector(BasePaymentConnector):
    code = "craftgate"
    display_name = "Craftgate"

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
                "Craftgate live charge: %s %s -> %s (mock fallback)",
                amount, currency, self.params.endpoint_url,
            )
        return ChargeResult(
            ok=True,
            provider_ref=f"MOCK-CRAFTGATE-{uuid4().hex[:12]}",
        )

    async def refund(
        self, provider_ref: str, amount: Decimal, currency: str
    ) -> RefundResult:
        if self._is_live:
            logger.info(
                "Craftgate live refund: %s %s ref=%s (mock fallback)",
                amount, currency, provider_ref,
            )
        return RefundResult(
            ok=True,
            provider_ref=f"MOCK-CRAFTGATE-REF-{uuid4().hex[:12]}",
        )

    async def test_connection(self) -> ChargeResult:
        if self._is_live:
            logger.info("Craftgate test_connection -> %s (mock fallback)", self.params.endpoint_url)
        return ChargeResult(ok=True, provider_ref="MOCK-CRAFTGATE-TEST")
