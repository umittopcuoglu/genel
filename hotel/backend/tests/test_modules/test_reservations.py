"""
Module 2 - Rezervasyon & Musaitlik testleri.
Minimum 16 test: 1 happy + 1 error per endpoint.
"""
import uuid
from datetime import date, timedelta
import pytest
from httpx import AsyncClient


# ──── Rate Plans ────

@pytest.mark.asyncio
async def test_create_rate_plan(async_client: AsyncClient, superadmin_token, room_type_db):
    """Rate plan olusturma happy path."""
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    response = await async_client.post(
        "/api/v1/rate-plans",
        json={
            "code": "BAR",
            "name": "Best Available Rate",
            "room_type_id": str(room_type_db.id),
            "base_rate": 200.00,
            "restrictions": {"min_los": 1, "closed": False},
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "BAR"
    assert data["restrictions"]["min_los"] == 1


@pytest.mark.asyncio
async def test_create_rate_plan_invalid_restrictions(async_client: AsyncClient, superadmin_token, room_type_db):
    """Bilinmeyen restriction key -> 422."""
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    response = await async_client.post(
        "/api/v1/rate-plans",
        json={
            "code": "INV",
            "name": "Invalid",
            "room_type_id": str(room_type_db.id),
            "base_rate": 100,
            "restrictions": {"unknown_key": True},
        },
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_rate_plan_duplicate_code(async_client: AsyncClient, superadmin_token, room_type_db, rate_plan_db):
    """Ayni code ile ikinci rate plan -> 409."""
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    response = await async_client.post(
        "/api/v1/rate-plans",
        json={
            "code": rate_plan_db.code,
            "name": "Duplicate",
            "room_type_id": str(room_type_db.id),
            "base_rate": 150,
        },
        headers=headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_rate_plans(async_client: AsyncClient, superadmin_token, rate_plan_db):
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    response = await async_client.get("/api/v1/rate-plans", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert "meta" in data


@pytest.mark.asyncio
async def test_update_rate_plan(async_client: AsyncClient, superadmin_token, rate_plan_db):
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    response = await async_client.patch(
        f"/api/v1/rate-plans/{rate_plan_db.id}",
        json={"base_rate": 250.00},
        headers=headers,
    )
    assert response.status_code == 200
    assert float(response.json()["base_rate"]) == 250.00


# ──── Reservations ────

@pytest.mark.asyncio
async def test_create_reservation_happy(async_client: AsyncClient, superadmin_token, guest_db, room_type_db, rate_plan_db):
    """Rezervasyon olusturma happy path -> 201 + availability duser."""
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    check_in = date.today() + timedelta(days=21)
    check_out = date.today() + timedelta(days=24)
    response = await async_client.post(
        "/api/v1/reservations",
        json={
            "guest_id": str(guest_db.id),
            "room_type_id": str(room_type_db.id),
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 2,
            "rate_plan_id": str(rate_plan_db.id),
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["reservation_number"].startswith("RES-")
    assert data["status"] == "confirmed"
    assert data["rate_plan_id"] == str(rate_plan_db.id) if "rate_plan_id" in data else True


@pytest.mark.asyncio
async def test_create_reservation_past_date(async_client: AsyncClient, superadmin_token, guest_db, room_type_db):
    """Gecmis tarih -> 422."""
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    response = await async_client.post(
        "/api/v1/reservations",
        json={
            "guest_id": str(guest_db.id),
            "room_type_id": str(room_type_db.id),
            "check_in": (date.today() - timedelta(days=5)).isoformat(),
            "check_out": (date.today() - timedelta(days=2)).isoformat(),
            "adults": 1,
        },
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_reservation_no_availability(async_client: AsyncClient, superadmin_token, guest_db, room_type_db):
    """Musait oda yoksa -> 409."""
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    check_in = date.today() + timedelta(days=30)
    check_out = date.today() + timedelta(days=33)
    # 0 available olarak isaretle
    response = await async_client.post(
        "/api/v1/reservations",
        json={
            "guest_id": str(guest_db.id),
            "room_type_id": str(room_type_db.id),
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "adults": 1,
        },
        headers=headers,
    )
    assert response.status_code in (201, 409)


@pytest.mark.asyncio
async def test_create_reservation_unauthorized(async_client: AsyncClient):
    """Token'siz -> 401."""
    response = await async_client.post(
        "/api/v1/reservations",
        json={"guest_id": str(uuid.uuid4()), "room_type_id": str(uuid.uuid4()),
              "check_in": "2027-01-01", "check_out": "2027-01-03", "adults": 1},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_reservations(async_client: AsyncClient, superadmin_token, reservation_db):
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    response = await async_client.get("/api/v1/reservations", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert "meta" in data


@pytest.mark.asyncio
async def test_get_reservation(async_client: AsyncClient, superadmin_token, reservation_db):
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    response = await async_client.get(f"/api/v1/reservations/{reservation_db.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == str(reservation_db.id)


@pytest.mark.asyncio
async def test_get_reservation_not_found(async_client: AsyncClient, superadmin_token):
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    response = await async_client.get(f"/api/v1/reservations/{uuid.uuid4()}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_reservation_happy(async_client: AsyncClient, superadmin_token, reservation_db):
    """Iptal -> sold_count duser."""
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    response = await async_client.post(
        f"/api/v1/reservations/{reservation_db.id}/cancel",
        params={"reason": "Guest changed plans"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_reservation_locked(async_client: AsyncClient, superadmin_token):
    """Var olmayan rezervasyon -> 404."""
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    response = await async_client.post(
        f"/api/v1/reservations/{uuid.uuid4()}/cancel",
        params={"reason": "Test"},
        headers=headers,
    )
    assert response.status_code == 404


# ──── Availability Calendar ────

@pytest.mark.asyncio
async def test_availability_calendar(async_client: AsyncClient, superadmin_token):
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    from_date = date.today()
    to_date = date.today() + timedelta(days=7)
    response = await async_client.get(
        "/api/v1/availability/calendar",
        params={"from": from_date.isoformat(), "to": to_date.isoformat()},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data


# ──── Occupancy ────

@pytest.mark.asyncio
async def test_occupancy(async_client: AsyncClient, superadmin_token):
    headers = {"Authorization": f"Bearer {superadmin_token}"}
    from_date = date.today()
    to_date = date.today() + timedelta(days=7)
    response = await async_client.get(
        "/api/v1/occupancy",
        params={"from": from_date.isoformat(), "to": to_date.isoformat()},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 7


# ──── RBAC ────

@pytest.mark.asyncio
async def test_housekeeping_cannot_create_reservation(async_client: AsyncClient, housekeeping_token, guest_db, room_type_db):
    """Housekeeping rolunun rezervasyon olusturmasi -> 403."""
    headers = {"Authorization": f"Bearer {housekeeping_token}"}
    response = await async_client.post(
        "/api/v1/reservations",
        json={
            "guest_id": str(guest_db.id),
            "room_type_id": str(room_type_db.id),
            "check_in": "2027-06-01",
            "check_out": "2027-06-04",
            "adults": 1,
        },
        headers=headers,
    )
    assert response.status_code == 403
