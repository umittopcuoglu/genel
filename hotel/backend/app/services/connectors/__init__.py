"""OTA connector kayıt defteri.

Yeni bir OTA eklemek için:
  1. `BaseOTAConnector` türevi bir sınıf yaz (ör. `agoda.AgodaConnector`).
  2. `register_connector('agoda', AgodaConnector)` ile kaydet.
  3. Channel modelinde `code='agoda'` ile kanal kaydı aç + integration_setting ekle.
  Core kodunda hiçbir değişiklik gerekmez (plug-in mantığı).
"""
from __future__ import annotations

from typing import Type

from app.services.connectors.base import BaseOTAConnector
from app.services.connectors.booking import BookingConnector
from app.services.connectors.expedia import ExpediaConnector
from app.services.connectors.agoda import AgodaConnector


_REGISTRY: dict[str, Type[BaseOTAConnector]] = {}


def register_connector(code: str, cls: Type[BaseOTAConnector]) -> None:
    _REGISTRY[code.lower()] = cls


def get_connector(code: str) -> Type[BaseOTAConnector] | None:
    return _REGISTRY.get(code.lower())


def available_connectors() -> list[str]:
    return sorted(_REGISTRY.keys())


# Built-in connector kayıtları
register_connector("booking", BookingConnector)
register_connector("expedia", ExpediaConnector)
register_connector("agoda", AgodaConnector)

__all__ = [
    "BaseOTAConnector",
    "register_connector",
    "get_connector",
    "available_connectors",
]
