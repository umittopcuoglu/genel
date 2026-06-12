"""EventBus + Connector pattern testleri."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.events import (
    CheckInCompleted,
    CheckOutCompleted,
    DomainEvent,
    EventBus,
    PaymentSucceeded,
    ReservationCancelled,
    ReservationCreated,
    events as global_events,
)
from app.services.connectors import (
    available_connectors,
    get_connector,
    register_connector,
)
from app.services.connectors.base import (
    AvailabilityPayload,
    BaseOTAConnector,
    ConnectorParams,
    SyncResult,
)


# ── EventBus unit ──

@pytest.mark.asyncio
async def test_event_bus_basic_dispatch():
    bus = EventBus()
    captured: list[ReservationCreated] = []

    @bus.subscribe(ReservationCreated)
    async def h(evt: ReservationCreated):
        captured.append(evt)

    await bus.publish(ReservationCreated(reservation_id=uuid4(), guest_id=uuid4()))
    assert len(captured) == 1


@pytest.mark.asyncio
async def test_event_bus_multiple_handlers_fault_isolation():
    bus = EventBus()
    received = []

    @bus.subscribe(ReservationCreated)
    async def good(evt):
        received.append("good")

    @bus.subscribe(ReservationCreated)
    async def bad(evt):
        raise RuntimeError("kaboom")

    @bus.subscribe(ReservationCreated)
    async def good2(evt):
        received.append("good2")

    results = await bus.publish(ReservationCreated(reservation_id=uuid4()))
    # 3 handler çalıştı; kötü olan exception'la diğerlerini etkilemedi
    assert len(results) == 3
    assert "good" in received and "good2" in received
    assert any(isinstance(r, dict) and "error" in r for r in results)


@pytest.mark.asyncio
async def test_event_bus_sync_handler_supported():
    bus = EventBus()
    seen = []

    @bus.subscribe(ReservationCreated)
    def sync_handler(evt):
        seen.append(evt.reservation_id)

    await bus.publish(ReservationCreated(reservation_id=uuid4()))
    assert len(seen) == 1


@pytest.mark.asyncio
async def test_event_bus_context_kwargs_passed():
    bus = EventBus()
    captured = {}

    @bus.subscribe(ReservationCreated)
    async def h(evt, db=None):
        captured["db"] = db

    await bus.publish(ReservationCreated(reservation_id=uuid4()), db="FAKE_SESSION")
    assert captured["db"] == "FAKE_SESSION"


# ── Connector registry ──

def test_builtin_connectors_registered():
    avail = available_connectors()
    assert "booking" in avail
    assert "expedia" in avail
    assert "agoda" in avail


def test_unknown_connector_returns_none():
    assert get_connector("hocus-pocus") is None


def test_register_custom_connector():
    class CustomConnector(BaseOTAConnector):
        code = "tatilsepeti"

        async def test_connection(self):
            return SyncResult(ok=True)

        async def push_availability(self, items):
            return SyncResult(ok=True, pushed=len(items))

        async def pull_reservations(self, since=None):
            return []

        async def acknowledge_reservation(self, external_id):
            return SyncResult(ok=True)

    register_connector("tatilsepeti", CustomConnector)
    assert get_connector("tatilsepeti") is CustomConnector


# ── Connector behavior ──

@pytest.mark.asyncio
async def test_booking_connector_test_connection_ok():
    cls = get_connector("booking")
    c = cls(ConnectorParams(api_key="k", hotel_code="123", endpoint_url="https://x"))
    r = await c.test_connection()
    assert r.ok is True


@pytest.mark.asyncio
async def test_booking_connector_missing_params_fails():
    cls = get_connector("booking")
    c = cls(ConnectorParams())
    r = await c.test_connection()
    assert r.ok is False
    assert "eksik" in (r.error_message or "")


@pytest.mark.asyncio
async def test_connector_push_availability():
    cls = get_connector("expedia")
    c = cls(ConnectorParams(api_key="k"))
    payload = [
        AvailabilityPayload(
            room_type_code="DBL", date=date(2026, 7, 1), allotment=5, rate=Decimal("150.00")
        )
    ]
    r = await c.push_availability(payload)
    assert r.ok is True
    assert r.pushed == 1


# ── Global bus → CRM handler (event_handlers.py kayıtlı mı) ──

@pytest.mark.asyncio
async def test_global_bus_has_subscribers():
    """app.core.event_handlers import edildiğinde abonelikler kurulmalı."""
    # event_handlers main.py'da import ediliyor; testte garanti için tekrar import
    import app.core.event_handlers  # noqa: F401
    # En az 1 ReservationCreated abonesi olmalı (welcome + audit log)
    handlers = global_events._handlers.get(ReservationCreated, [])
    assert len(handlers) >= 2


@pytest.mark.asyncio
async def test_global_bus_publish_with_db_context_runs_handlers(db, guest_db):
    """Global bus üzerinden ReservationCreated yayınla, CRM handler'ı log üretmeli."""
    from sqlalchemy import select

    from app.models.crm import CommunicationLog
    import app.core.event_handlers  # noqa: F401

    evt = ReservationCreated(
        reservation_id=uuid4(),
        guest_id=guest_db.id,
        check_in="2026-07-01",
        check_out="2026-07-03",
        source="direct",
    )
    await global_events.publish(evt, db=db)
    await db.commit()

    res = await db.execute(
        select(CommunicationLog).where(CommunicationLog.guest_id == guest_db.id)
    )
    rows = list(res.scalars().all())
    assert any("Rezervasyon" in (r.subject or "") for r in rows)


# ── B1-B5: Yeni event tipleri ──

@pytest.mark.asyncio
async def test_check_in_event_dispatch():
    """CheckInCompleted event'i bus üzerinden yayınlanabilir."""
    bus = EventBus()
    seen = []

    @bus.subscribe(CheckInCompleted)
    async def h(evt):
        seen.append(evt.reservation_id)

    evt = CheckInCompleted(reservation_id=uuid4(), guest_id=uuid4(), room_id=uuid4())
    await bus.publish(evt)
    assert len(seen) == 1


@pytest.mark.asyncio
async def test_check_out_event_dispatch():
    bus = EventBus()
    seen = []

    @bus.subscribe(CheckOutCompleted)
    async def h(evt):
        seen.append(evt.folio_total)

    await bus.publish(CheckOutCompleted(reservation_id=uuid4(), folio_total=1500.0))
    assert seen == [1500.0]


@pytest.mark.asyncio
async def test_reservation_cancelled_event_dispatch():
    bus = EventBus()
    seen = []

    @bus.subscribe(ReservationCancelled)
    async def h(evt):
        seen.append(evt.reason)

    await bus.publish(ReservationCancelled(reservation_id=uuid4(), reason="customer_request"))
    assert seen == ["customer_request"]


@pytest.mark.asyncio
async def test_payment_succeeded_event_dispatch():
    bus = EventBus()
    seen = []

    @bus.subscribe(PaymentSucceeded)
    async def h(evt):
        seen.append(evt.amount)

    await bus.publish(PaymentSucceeded(txn_id=uuid4(), folio_id=uuid4(), amount=2500.0))
    assert seen == [2500.0]


def test_global_bus_has_all_event_subscribers():
    """Tüm yeni event tipleri için en az 1 subscriber kayıtlı olmalı."""
    import app.core.event_handlers  # noqa: F401
    assert len(global_events._handlers.get(CheckInCompleted, [])) >= 1
    assert len(global_events._handlers.get(CheckOutCompleted, [])) >= 1
    assert len(global_events._handlers.get(ReservationCancelled, [])) >= 1
    assert len(global_events._handlers.get(PaymentSucceeded, [])) >= 1


def test_global_bus_has_channel_sync_handler():
    """B4: ReservationCreated için channel_sync_on_reservation handler'ı kayıtlı olmalı."""
    import app.core.event_handlers  # noqa: F401
    handlers = global_events._handlers.get(ReservationCreated, [])
    names = [getattr(h, "__name__", "") for h in handlers]
    assert "channel_sync_on_reservation" in names
