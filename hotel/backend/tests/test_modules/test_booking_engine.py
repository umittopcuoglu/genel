"""Booking Engine (public) + Channel Sync testleri — HotelRunner/Cloudbeds denklemi."""
from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from app.models.reservation_ext import Availability


def _dates(days_ahead: int = 7, nights: int = 2) -> tuple[str, str]:
    ci = date.today() + timedelta(days=days_ahead)
    co = ci + timedelta(days=nights)
    return ci.isoformat(), co.isoformat()


@pytest.fixture
async def inventory(db, room_type_db):
    """10 odalık 14 günlük envanter (Deluxe Sea View senaryosu)."""
    start = date.today()
    for i in range(14):
        db.add(Availability(room_type_id=room_type_db.id, date=start + timedelta(days=i), available_count=10, sold_count=0))
    await db.commit()
    return room_type_db


@pytest.fixture
async def booking_channel(async_client, superadmin_headers):
    """Aktif bir OTA kanalı (sync log hedefi)."""
    resp = await async_client.post(
        "/api/v1/channels",
        json={
            "name": "Booking.com",
            "channel_type": "ota",
            "credentials": "test-key",
            "api_base_url": "https://distribution-xml.booking.com",
        },
        headers=superadmin_headers,
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


BOOKING_BODY = {
    "adults": 2,
    "children": 0,
    "first_name": "Ayşe",
    "last_name": "Yılmaz",
    "email": "ayse@example.com",
    "phone": "+905551112233",
}


# ── Müsaitlik arama ──

@pytest.mark.asyncio
async def test_search_availability_public(client: AsyncClient, inventory):
    ci, co = _dates()
    resp = await client.get(f"/api/v1/public/availability?check_in={ci}&check_out={co}&adults=2")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    item = items[0]
    assert item["rooms_left"] == 10
    assert item["nights"] == 2
    assert float(item["total_price"]) == float(item["nightly_rate"]) * 2


@pytest.mark.asyncio
async def test_search_invalid_dates(client: AsyncClient, inventory):
    resp = await client.get("/api/v1/public/availability?check_in=2020-01-01&check_out=2020-01-03")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_no_inventory_returns_empty(client: AsyncClient, room_type_db):
    ci, co = _dates()
    resp = await client.get(f"/api/v1/public/availability?check_in={ci}&check_out={co}")
    assert resp.status_code == 200
    assert resp.json() == []


# ── Rezervasyon ──

@pytest.mark.asyncio
async def test_create_public_booking_no_auth(client: AsyncClient, inventory):
    ci, co = _dates()
    resp = await client.post(
        "/api/v1/public/bookings",
        json={**BOOKING_BODY, "room_type_id": str(inventory.id), "check_in": ci, "check_out": co},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["reservation_number"].startswith("WEB-")
    assert body["status"] == "confirmed"
    assert body["guest_name"] == "Ayşe Yılmaz"


@pytest.mark.asyncio
async def test_booking_decrements_inventory(client: AsyncClient, inventory):
    ci, co = _dates()
    await client.post(
        "/api/v1/public/bookings",
        json={**BOOKING_BODY, "room_type_id": str(inventory.id), "check_in": ci, "check_out": co},
    )
    resp = await client.get(f"/api/v1/public/availability?check_in={ci}&check_out={co}")
    assert resp.json()[0]["rooms_left"] == 9


@pytest.mark.asyncio
async def test_overbooking_blocked(client: AsyncClient, db, room_type_db):
    """Son oda satılınca tüm kanallarda satış kapanır — 409 döner."""
    start = date.today() + timedelta(days=7)
    for i in range(2):
        db.add(Availability(room_type_id=room_type_db.id, date=start + timedelta(days=i), available_count=1, sold_count=0))
    await db.commit()
    ci, co = start.isoformat(), (start + timedelta(days=2)).isoformat()

    first = await client.post(
        "/api/v1/public/bookings",
        json={**BOOKING_BODY, "room_type_id": str(room_type_db.id), "check_in": ci, "check_out": co},
    )
    assert first.status_code == 201
    second = await client.post(
        "/api/v1/public/bookings",
        json={**BOOKING_BODY, "email": "baska@example.com", "room_type_id": str(room_type_db.id), "check_in": ci, "check_out": co},
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_booking_lookup_requires_matching_email(client: AsyncClient, inventory):
    ci, co = _dates()
    created = await client.post(
        "/api/v1/public/bookings",
        json={**BOOKING_BODY, "room_type_id": str(inventory.id), "check_in": ci, "check_out": co},
    )
    number = created.json()["reservation_number"]

    ok = await client.get(f"/api/v1/public/bookings/{number}?email=ayse@example.com")
    assert ok.status_code == 200
    assert ok.json()["reservation_number"] == number

    wrong = await client.get(f"/api/v1/public/bookings/{number}?email=yanlis@example.com")
    assert wrong.status_code == 404


# ── Channel Manager senkronu ──

@pytest.mark.asyncio
async def test_booking_pushes_inventory_to_channels(client: AsyncClient, inventory, booking_channel, superadmin_headers):
    """Rezervasyon sonrası tüm aktif kanallara push loglanır (overbooking koruması)."""
    ci, co = _dates()
    resp = await client.post(
        "/api/v1/public/bookings",
        json={**BOOKING_BODY, "room_type_id": str(inventory.id), "check_in": ci, "check_out": co},
    )
    assert resp.status_code == 201
    assert resp.json()["channels_notified"] >= 1

    from sqlalchemy import select
    from app.models.channel_sync_log import ChannelSyncLog
    from tests.conftest import TestingSessionLocal

    async with TestingSessionLocal() as session:
        logs = (await session.execute(select(ChannelSyncLog))).scalars().all()
        assert any(l.sync_type == "inventory_push:reservation" and l.status == "success" for l in logs)


@pytest.mark.asyncio
async def test_staff_reservation_also_syncs_channels(client: AsyncClient, inventory, booking_channel, superadmin_headers, guest_db):
    """Resepsiyon rezervasyonu da kanal senkronunu tetikler."""
    ci, co = _dates(days_ahead=10)
    resp = await client.post(
        "/api/v1/reservations",
        json={"guest_id": str(guest_db.id), "room_type_id": str(inventory.id), "check_in": ci, "check_out": co, "adults": 1},
        headers=superadmin_headers,
    )
    assert resp.status_code == 201, resp.text

    from sqlalchemy import select
    from app.models.channel_sync_log import ChannelSyncLog
    from tests.conftest import TestingSessionLocal

    async with TestingSessionLocal() as session:
        logs = (await session.execute(select(ChannelSyncLog))).scalars().all()
        assert len(logs) >= 1


@pytest.mark.asyncio
async def test_payment_gateway_in_specs(client: AsyncClient, superadmin_headers):
    resp = await client.get("/api/v1/integrations/specs", headers=superadmin_headers)
    specs = resp.json()
    assert "payment_gateway" in specs
    assert any(p["key"] == "provider" for p in specs["payment_gateway"])
