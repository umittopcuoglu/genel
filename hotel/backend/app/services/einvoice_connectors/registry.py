"""E-fatura connector kayıt defteri.

Yeni bir entegratör eklemek için:
  1. `BaseEInvoiceConnector` türevi bir sınıf yaz (ör. `foriba.ForibaConnector`).
  2. `register_einvoice_connector('foriba', ForibaConnector)` ile kaydet.
  3. IntegrationSetting'de `provider='foriba'` olarak ayarla.
  Core kodunda hiçbir değişiklik gerekmez (plug-in mantığı).
"""
from __future__ import annotations

from typing import Type

from app.services.einvoice_connectors import BaseEInvoiceConnector
from app.services.einvoice_connectors.foriba import ForibaConnector
from app.services.einvoice_connectors.logo import LogoConnector
from app.services.einvoice_connectors.uyumsoft import UyumsoftConnector
from app.services.einvoice_connectors.izibiz import IzibizConnector


_REGISTRY: dict[str, Type[BaseEInvoiceConnector]] = {}


def register_einvoice_connector(code: str, cls: Type[BaseEInvoiceConnector]) -> None:
    _REGISTRY[code.lower()] = cls


def get_einvoice_connector(code: str) -> Type[BaseEInvoiceConnector] | None:
    """Provider koduna göre connector sınıfını döndürür."""
    return _REGISTRY.get(code.lower())


def available_einvoice_connectors() -> list[str]:
    return sorted(_REGISTRY.keys())


# Built-in connector kayıtları
register_einvoice_connector("foriba", ForibaConnector)
register_einvoice_connector("logo", LogoConnector)
register_einvoice_connector("uyumsoft", UyumsoftConnector)
register_einvoice_connector("izibiz", IzibizConnector)

__all__ = [
    "BaseEInvoiceConnector",
    "register_einvoice_connector",
    "get_einvoice_connector",
    "available_einvoice_connectors",
]
