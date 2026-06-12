"""Expedia EQC connector — MOCK."""
from __future__ import annotations

import secrets
from datetime import date

from app.services.connectors.base import (
    AvailabilityPayload,
    BaseOTAConnector,
    InboundReservation,
    SyncResult,
)


class ExpediaConnector(BaseOTAConnector):
    code = "expedia"

    async def test_connection(self) -> SyncResult:
        if not self.params.api_key:
            return SyncResult(ok=False, error_message="api_key eksik")
        return SyncResult(ok=True, raw_response={"provider": "expedia", "status": "ready"})

    async def push_availability(self, items: list[AvailabilityPayload]) -> SyncResult:
        return SyncResult(
            ok=True,
            pushed=len(items),
            raw_response={"ref": f"EXP-{secrets.token_hex(4)}", "count": len(items)},
        )

    async def pull_reservations(self, since: date | None = None) -> list[InboundReservation]:
        return []

    async def acknowledge_reservation(self, external_id: str) -> SyncResult:
        return SyncResult(ok=True, raw_response={"ack": external_id})
