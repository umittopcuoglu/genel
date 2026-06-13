"""OTA connector için soyut taban sınıf.

Her connector aynı arayüzü uygular. Channel sync orchestrator bu arayüze
dayanır; concrete sınıflar sadece HTTP detaylarını farklılaştırır.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass
class ConnectorParams:
    """Entegrasyon kaydından çözülmüş, provider-agnostik parametre kabı."""
    api_key: str = ""
    hotel_code: str = ""
    endpoint_url: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class AvailabilityPayload:
    room_type_code: str
    date: date
    allotment: int
    rate: Decimal
    closed: bool = False


@dataclass
class InboundReservation:
    """OTA'dan çekilen ham rezervasyon — adapter PMS modeline çevirir."""
    external_id: str
    guest_first_name: str
    guest_last_name: str
    guest_email: str | None
    check_in: date
    check_out: date
    room_type_code: str
    total_amount: Decimal
    raw: dict[str, Any]


@dataclass
class SyncResult:
    ok: bool
    pushed: int = 0
    pulled: int = 0
    error_message: str | None = None
    raw_response: Any = None


class BaseOTAConnector(ABC):
    """Tüm OTA connector'ları için sözleşme.

    Implementations:
      - test_connection(): canlı el sıkışma
      - push_availability(): allotment + rate gönder
      - pull_reservations(): yeni rezervasyonları çek
      - acknowledge_reservation(): OTA tarafına onay (idempotent)
    """

    code: str = ""

    def __init__(self, params: ConnectorParams) -> None:
        self.params = params

    @abstractmethod
    async def test_connection(self) -> SyncResult: ...

    @abstractmethod
    async def push_availability(
        self, items: list[AvailabilityPayload]
    ) -> SyncResult: ...

    @abstractmethod
    async def pull_reservations(self, since: date | None = None) -> list[InboundReservation]: ...

    @abstractmethod
    async def acknowledge_reservation(self, external_id: str) -> SyncResult: ...
