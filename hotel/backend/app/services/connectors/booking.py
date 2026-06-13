"""Booking.com connector — şu an MOCK; gerçek istekler için XML/REST geçişi
buraya delege edilir. Public arayüz BaseOTAConnector ile aynı."""
from __future__ import annotations

import secrets
from datetime import date
from typing import Any

from app.services.connectors.base import (
    AvailabilityPayload,
    BaseOTAConnector,
    InboundReservation,
    SyncResult,
)


class BookingConnector(BaseOTAConnector):
    code = "booking"

    async def test_connection(self) -> SyncResult:
        if not self.params.api_key or not self.params.hotel_code:
            return SyncResult(ok=False, error_message="api_key veya hotel_code eksik")
        return SyncResult(ok=True, raw_response={"provider": "booking", "status": "ready"})

    async def push_availability(self, items: list[AvailabilityPayload]) -> SyncResult:
        # MOCK: gerçek XML POST burada olur
        return SyncResult(
            ok=True,
            pushed=len(items),
            raw_response={"ref": f"BKG-{secrets.token_hex(4)}", "count": len(items)},
        )

    async def pull_reservations(self, since: date | None = None) -> list[InboundReservation]:
        return []  # MOCK: yeni rezervasyon yok

    async def acknowledge_reservation(self, external_id: str) -> SyncResult:
        return SyncResult(ok=True, raw_response={"ack": external_id})
