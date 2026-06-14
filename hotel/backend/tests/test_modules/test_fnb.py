"""TASK-016 — F&B / POS modülü testleri."""
import pytest
from uuid import uuid4
from httpx import AsyncClient


# ── Outlet ──
@pytest.mark.asyncio
async def test_create_outlet(client: AsyncClient, manager_headers: dict):
    resp = await client.post(
        "/api/v1/fnb/outlets",
        json={"name": "Lobby Bar", "outlet_type": "bar"},
        headers=manager_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "Lobby Bar"
    assert data["is_open"] is True


@pytest.mark.asyncio
async def test_list_outlets(client: AsyncClient, manager_headers: dict):
    await client.post(
        "/api/v1/fnb/outlets",
        json={"name": "Main Restaurant", "outlet_type": "restaurant"},
        headers=manager_headers,
    )
    resp = await client.get("/api/v1/fnb/outlets")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_outlet_unauthorized(client: AsyncClient, frontdesk_headers: dict):
    """frontdesk outlet oluşturamaz → 403."""
    resp = await client.post(
        "/api/v1/fnb/outlets",
        json={"name": "X", "outlet_type": "bar"},
        headers=frontdesk_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_outlet_no_token(client: AsyncClient):
    resp = await client.post(
        "/api/v1/fnb/outlets",
        json={"name": "X", "outlet_type": "bar"},
    )
    assert resp.status_code == 401


# ── Menu ──
@pytest.mark.asyncio
async def test_create_menu_item(client: AsyncClient, manager_headers: dict):
    outlet = await client.post(
        "/api/v1/fnb/outlets",
        json={"name": "Pool Bar", "outlet_type": "bar"},
        headers=manager_headers,
    )
    outlet_id = outlet.json()["id"]
    resp = await client.post(
        "/api/v1/fnb/menu-items",
        json={"outlet_id": outlet_id, "name": "Mojito", "category": "beverage", "price": 120.0, "cost": 30.0},
        headers=manager_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["name"] == "Mojito"


@pytest.mark.asyncio
async def test_list_menu_items_filtered(client: AsyncClient, manager_headers: dict):
    outlet = await client.post(
        "/api/v1/fnb/outlets",
        json={"name": "Cafe", "outlet_type": "cafe"},
        headers=manager_headers,
    )
    outlet_id = outlet.json()["id"]
    await client.post(
        "/api/v1/fnb/menu-items",
        json={"outlet_id": outlet_id, "name": "Espresso", "category": "beverage", "price": 45.0},
        headers=manager_headers,
    )
    resp = await client.get(f"/api/v1/fnb/menu-items?outlet_id={outlet_id}")
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()]
    assert "Espresso" in names


# ── Check flow ──
@pytest.mark.asyncio
async def test_check_full_flow(client: AsyncClient, manager_headers: dict):
    """Adisyon aç → satır ekle → toplam güncellenir → kapat."""
    outlet = await client.post(
        "/api/v1/fnb/outlets",
        json={"name": "Bistro", "outlet_type": "restaurant"},
        headers=manager_headers,
    )
    outlet_id = outlet.json()["id"]
    item = await client.post(
        "/api/v1/fnb/menu-items",
        json={"outlet_id": outlet_id, "name": "Steak", "category": "main", "price": 300.0},
        headers=manager_headers,
    )
    item_id = item.json()["id"]

    check = await client.post(
        "/api/v1/fnb/checks",
        json={"outlet_id": outlet_id, "table_no": "T1"},
        headers=manager_headers,
    )
    assert check.status_code == 201
    check_id = check.json()["id"]

    added = await client.post(
        f"/api/v1/fnb/checks/{check_id}/items",
        json={"menu_item_id": item_id, "qty": 2},
        headers=manager_headers,
    )
    assert added.status_code == 200, added.text
    assert float(added.json()["total"]) == 600.0
    assert len(added.json()["items"]) == 1

    closed = await client.post(f"/api/v1/fnb/checks/{check_id}/close", headers=manager_headers)
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"


@pytest.mark.asyncio
async def test_add_item_to_closed_check_409(client: AsyncClient, manager_headers: dict):
    outlet = await client.post(
        "/api/v1/fnb/outlets",
        json={"name": "Grill", "outlet_type": "restaurant"},
        headers=manager_headers,
    )
    outlet_id = outlet.json()["id"]
    item = await client.post(
        "/api/v1/fnb/menu-items",
        json={"outlet_id": outlet_id, "name": "Burger", "category": "main", "price": 150.0},
        headers=manager_headers,
    )
    item_id = item.json()["id"]
    check = await client.post(
        "/api/v1/fnb/checks", json={"outlet_id": outlet_id}, headers=manager_headers
    )
    check_id = check.json()["id"]
    await client.post(f"/api/v1/fnb/checks/{check_id}/close", headers=manager_headers)
    resp = await client.post(
        f"/api/v1/fnb/checks/{check_id}/items",
        json={"menu_item_id": item_id, "qty": 1},
        headers=manager_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_room_charge_to_folio(client: AsyncClient, manager_headers: dict, folio_db):
    """Adisyon → oda folio'suna fnb satırı yansır."""
    outlet = await client.post(
        "/api/v1/fnb/outlets",
        json={"name": "Room Service", "outlet_type": "room_service"},
        headers=manager_headers,
    )
    outlet_id = outlet.json()["id"]
    item = await client.post(
        "/api/v1/fnb/menu-items",
        json={"outlet_id": outlet_id, "name": "Club Sandwich", "category": "main", "price": 200.0},
        headers=manager_headers,
    )
    item_id = item.json()["id"]
    check = await client.post(
        "/api/v1/fnb/checks", json={"outlet_id": outlet_id, "room_no": "101"}, headers=manager_headers
    )
    check_id = check.json()["id"]
    await client.post(
        f"/api/v1/fnb/checks/{check_id}/items",
        json={"menu_item_id": item_id, "qty": 1},
        headers=manager_headers,
    )
    resp = await client.post(
        f"/api/v1/fnb/checks/{check_id}/room-charge",
        json={"folio_id": str(folio_db.id)},
        headers=manager_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["folio_id"] == str(folio_db.id)
    assert resp.json()["status"] == "closed"


@pytest.mark.asyncio
async def test_room_charge_missing_folio_404(client: AsyncClient, manager_headers: dict):
    outlet = await client.post(
        "/api/v1/fnb/outlets",
        json={"name": "Snack", "outlet_type": "cafe"},
        headers=manager_headers,
    )
    outlet_id = outlet.json()["id"]
    check = await client.post(
        "/api/v1/fnb/checks", json={"outlet_id": outlet_id}, headers=manager_headers
    )
    check_id = check.json()["id"]
    resp = await client.post(
        f"/api/v1/fnb/checks/{check_id}/room-charge",
        json={"folio_id": str(uuid4())},
        headers=manager_headers,
    )
    assert resp.status_code == 404


# ── Stock ──
@pytest.mark.asyncio
async def test_stock_create_and_low_stock(client: AsyncClient, manager_headers: dict):
    resp = await client.post(
        "/api/v1/fnb/stock-items",
        json={"name": "Tomato", "unit": "kg", "quantity": 5, "reorder_level": 10},
        headers=manager_headers,
    )
    assert resp.status_code == 201, resp.text
    low = await client.get("/api/v1/fnb/stock-items/low")
    assert low.status_code == 200
    names = [s["name"] for s in low.json()]
    assert "Tomato" in names


@pytest.mark.asyncio
async def test_stock_movement_out_insufficient_422(client: AsyncClient, manager_headers: dict):
    item = await client.post(
        "/api/v1/fnb/stock-items",
        json={"name": "Wine", "unit": "lt", "quantity": 2, "reorder_level": 1},
        headers=manager_headers,
    )
    item_id = item.json()["id"]
    resp = await client.post(
        "/api/v1/fnb/stock-movements",
        json={"stock_item_id": item_id, "movement_type": "out", "quantity": 10},
        headers=manager_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_stock_movement_in(client: AsyncClient, manager_headers: dict):
    item = await client.post(
        "/api/v1/fnb/stock-items",
        json={"name": "Flour", "unit": "kg", "quantity": 5, "reorder_level": 2},
        headers=manager_headers,
    )
    item_id = item.json()["id"]
    resp = await client.post(
        "/api/v1/fnb/stock-movements",
        json={"stock_item_id": item_id, "movement_type": "in", "quantity": 10},
        headers=manager_headers,
    )
    assert resp.status_code == 200
    assert float(resp.json()["quantity"]) == 15.0
