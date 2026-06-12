"""TASK-014 Groups & Events tests."""
import pytest
from uuid import uuid4
from datetime import date, datetime, timedelta
from decimal import Decimal
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_group(client: AsyncClient, manager_headers: dict):
    """Yeni grup oluştur."""
    response = await client.post(
        "/api/v1/groups",
        json={
            "name": "Touresco Conference 2026",
            "block_start_date": "2026-07-01",
            "block_end_date": "2026-07-05",
            "pax_count": 50,
            "discount_rate": 10.0,
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Touresco Conference 2026"
    assert data["status"] == "inquiry"
    assert data["group_folio_id"] is not None  # Master folio created


@pytest.mark.asyncio
async def test_get_group(client: AsyncClient, manager_headers: dict, groups_fixture):
    """Grup detaylarını getir."""
    group_id = groups_fixture["group_id"]
    response = await client.get(
        f"/api/v1/groups/{group_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(group_id)
    assert data["name"] == "Test Group"


@pytest.mark.asyncio
async def test_update_group_status_inquiry_to_confirmed(
    client: AsyncClient, manager_headers: dict, groups_fixture
):
    """Grup durumunu inquiry'den confirmed'e güncelle."""
    group_id = groups_fixture["group_id"]

    # Add a room block first
    await client.post(
        f"/api/v1/groups/{group_id}/room-blocks",
        json={
            "room_type_id": str(groups_fixture["room_type_id"]),
            "qty_required": 5,
            "qty_confirmed": 5,  # Must confirm all required
            "pickup_date": "2026-07-01",
            "release_date": "2026-07-05",
        },
        headers=manager_headers,
    )

    response = await client.patch(
        f"/api/v1/groups/{group_id}/status",
        json={"status": "confirmed"},
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_create_room_block(client: AsyncClient, manager_headers: dict, groups_fixture):
    """Grup için oda bloku ekle."""
    group_id = groups_fixture["group_id"]
    room_type_id = groups_fixture["room_type_id"]

    response = await client.post(
        f"/api/v1/groups/{group_id}/room-blocks",
        json={
            "room_type_id": str(room_type_id),
            "qty_required": 10,
            "pickup_date": "2026-07-01",
            "release_date": "2026-07-05",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["qty_required"] == 10
    assert data["qty_confirmed"] == 0
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_event(client: AsyncClient, manager_headers: dict, groups_fixture):
    """Grup için etkinlik oluştur."""
    group_id = groups_fixture["group_id"]

    response = await client.post(
        f"/api/v1/groups/{group_id}/events",
        json={
            "title": "Opening Gala Dinner",
            "event_type": "gala",
            "capacity_required": 100,
            "setup_type": "banquet",
            "start_datetime": "2026-07-01T19:00:00+03:00",
            "end_datetime": "2026-07-01T22:00:00+03:00",
            "catering_required": True,
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Opening Gala Dinner"
    assert data["event_type"] == "gala"
    assert data["catering_required"] is True


@pytest.mark.asyncio
async def test_import_rooming_list(client: AsyncClient, manager_headers: dict, groups_fixture):
    """Toplu rooming list import."""
    group_id = groups_fixture["group_id"]

    response = await client.post(
        f"/api/v1/groups/{group_id}/rooming-list/import",
        json=[
            {
                "guest_name": "John Smith",
                "guest_email": "john@example.com",
                "room_type_requested": "double",
                "checkin_date": "2026-07-01",
                "checkout_date": "2026-07-05",
            },
            {
                "guest_name": "Jane Doe",
                "guest_email": "jane@example.com",
                "room_type_requested": "single",
                "checkin_date": "2026-07-01",
                "checkout_date": "2026-07-05",
            },
        ],
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["imported_count"] == 2


@pytest.mark.asyncio
async def test_list_groups(client: AsyncClient, manager_headers: dict, groups_fixture):
    """Grupları listele."""
    response = await client.get(
        "/api/v1/groups",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_list_groups_with_status_filter(
    client: AsyncClient, manager_headers: dict, groups_fixture
):
    """Grupları durum filtresiyle listele."""
    response = await client.get(
        "/api/v1/groups?status=inquiry",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert all(g["status"] == "inquiry" for g in data)


@pytest.mark.asyncio
async def test_get_rooming_list(client: AsyncClient, manager_headers: dict, groups_fixture):
    """Grubun rooming list'ini getir."""
    group_id = groups_fixture["group_id"]

    # First import some rooming list
    await client.post(
        f"/api/v1/groups/{group_id}/rooming-list/import",
        json=[
            {
                "guest_name": "Alice Wonder",
                "room_type_requested": "deluxe",
                "checkin_date": "2026-07-01",
                "checkout_date": "2026-07-05",
            }
        ],
        headers=manager_headers,
    )

    response = await client.get(
        f"/api/v1/groups/{group_id}/rooming-list",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["guest_name"] == "Alice Wonder"


@pytest.mark.asyncio
async def test_release_room_block(client: AsyncClient, manager_headers: dict, groups_fixture):
    """Oda bloğunu serbest bırak."""
    group_id = groups_fixture["group_id"]
    room_type_id = groups_fixture["room_type_id"]

    # Create a room block
    create_response = await client.post(
        f"/api/v1/groups/{group_id}/room-blocks",
        json={
            "room_type_id": str(room_type_id),
            "qty_required": 5,
            "pickup_date": "2026-07-01",
            "release_date": "2026-07-05",
        },
        headers=manager_headers,
    )
    block_id = create_response.json()["id"]

    # Release it
    response = await client.patch(
        f"/api/v1/groups/{group_id}/room-blocks/{block_id}/release",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "released"


@pytest.mark.asyncio
async def test_insufficient_inventory_on_confirm(
    client: AsyncClient, manager_headers: dict, groups_fixture
):
    """Yetersiz envanterle status confirm'e çekinemez."""
    group_id = groups_fixture["group_id"]
    room_type_id = groups_fixture["room_type_id"]

    # Create a room block with unmet qty_confirmed
    await client.post(
        f"/api/v1/groups/{group_id}/room-blocks",
        json={
            "room_type_id": str(room_type_id),
            "qty_required": 10,
            "pickup_date": "2026-07-01",
            "release_date": "2026-07-05",
        },
        headers=manager_headers,
    )

    response = await client.patch(
        f"/api/v1/groups/{group_id}/status",
        json={"status": "confirmed"},
        headers=manager_headers,
    )
    # Should fail with 422 due to insufficient inventory
    assert response.status_code in [400, 422]
