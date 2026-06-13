from __future__ import annotations

from typing import TYPE_CHECKING

from .craftgate import CraftgateConnector
from .iyzico import IyzicoConnector
from .paytr import PayTRConnector
from .stripe import StripeConnector

if TYPE_CHECKING:
    from . import BasePaymentConnector, PaymentParams

CONNECTORS: dict[str, type[BasePaymentConnector]] = {
    "iyzico": IyzicoConnector,
    "stripe": StripeConnector,
    "paytr": PayTRConnector,
    "craftgate": CraftgateConnector,
}


def get_payment_connector(name: str, params: PaymentParams | None = None) -> BasePaymentConnector:
    cls = CONNECTORS.get(name)
    if cls is None:
        raise ValueError(f"Unknown payment provider: {name!r}. Available: {', '.join(CONNECTORS)}")
    if params is None:
        from . import PaymentParams
        params = PaymentParams(provider=name)
    return cls(params)
