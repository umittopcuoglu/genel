"""F&B / POS testleri: outlet, menu, check, post-to-folio, settle, void."""
import pytest


@pytest.fixture
async def outlet(async_client, manager_headers):
    r = await async_client.post(
        "/api/v1/fnb/outlets",
        json={"name": "Main Restaurant", "kind": "restaurant", "open_time": "07:00", "close_time": "23:00"},
        headers=manager_headers,
    )
    assert r.status_code == 201
    return r.json()


@pytest.fixture
async def menu_item(async_client, manager_headers, outlet):
    r = await async_client.post(
        "/api/v1/fnb/menu-items",
        json={"outlet_id": outlet["id"], "name": "Izgara Levrek", "category": "main", "price": "180.00"},
        headers=manager_headers,
    )
    assert r.status_code == 201
    return r.json()


@pytest.mark.asyncio
async def test_create_and_list_outlet(async_client, manager_headers):
    cr = await async_client.post(
        "/api/v1/fnb/outlets", json={"name": "Lobby Cafe"}, headers=manager_headers
    )
    assert cr.status_code == 201
    lst = await async_client.get("/api/v1/fnb/outlets", headers=manager_headers)
    assert any(o["name"] == "Lobby Cafe" for o in lst.json())


@pytest.mark.asyncio
async def test_menu_create_and_list(async_client, manager_headers, outlet):
    cr = await async_client.post(
        "/api/v1/fnb/menu-items",
        json={"outlet_id": outlet["id"], "name": "Tiramisu", "category": "dessert", "price": "120"},
        headers=manager_headers,
    )
    assert cr.status_code == 201
    lst = await async_client.get(f"/api/v1/fnb/outlets/{outlet['id']}/menu", headers=manager_headers)
    assert len(lst.json()) >= 1


@pytest.mark.asyncio
async def test_check_lifecycle_settle_cash(async_client, frontdesk_headers, outlet, menu_item):
    ch = await async_client.post(
        "/api/v1/fnb/checks",
        json={"outlet_id": outlet["id"], "table_no": "5"},
        headers=frontdesk_headers,
    )
    assert ch.status_code == 201
    cid = ch.json()["id"]
    # 2 adet ekle
    add = await async_client.post(
        f"/api/v1/fnb/checks/{cid}/items",
        json={"menu_item_id": menu_item["id"], "qty": 2},
        headers=frontdesk_headers,
    )
    assert add.status_code == 200
    data = add.json()
    assert float(data["total"]) == 360.00
    assert len(data["items"]) == 1
    # Ödeme al
    pay = await async_client.post(f"/api/v1/fnb/checks/{cid}/settle-cash", headers=frontdesk_headers)
    assert pay.json()["status"] == "paid"


@pytest.mark.asyncio
async def test_post_to_folio(async_client, frontdesk_headers, outlet, menu_item, guest_db, db):
    from app.models.finance import Folio
    folio = Folio(guest_id=guest_db.id, total=0, balance=0)
    db.add(folio)
    await db.commit()
    await db.refresh(folio)

    ch = await async_client.post(
        "/api/v1/fnb/checks",
        json={"outlet_id": outlet["id"], "guest_id": str(guest_db.id)},
        headers=frontdesk_headers,
    )
    cid = ch.json()["id"]
    await async_client.post(
        f"/api/v1/fnb/checks/{cid}/items",
        json={"menu_item_id": menu_item["id"], "qty": 1},
        headers=frontdesk_headers,
    )
    post = await async_client.post(
        f"/api/v1/fnb/checks/{cid}/post-to-folio",
        json={"folio_id": str(folio.id)},
        headers=frontdesk_headers,
    )
    assert post.status_code == 200
    assert post.json()["status"] == "posted_to_folio"


@pytest.mark.asyncio
async def test_void_check(async_client, frontdesk_headers, outlet):
    ch = await async_client.post(
        "/api/v1/fnb/checks", json={"outlet_id": outlet["id"]}, headers=frontdesk_headers
    )
    cid = ch.json()["id"]
    v = await async_client.post(f"/api/v1/fnb/checks/{cid}/void", headers=frontdesk_headers)
    assert v.json()["status"] == "voided"


@pytest.mark.asyncio
async def test_cannot_add_to_paid_check(async_client, frontdesk_headers, outlet, menu_item):
    ch = await async_client.post(
        "/api/v1/fnb/checks", json={"outlet_id": outlet["id"]}, headers=frontdesk_headers
    )
    cid = ch.json()["id"]
    await async_client.post(f"/api/v1/fnb/checks/{cid}/settle-cash", headers=frontdesk_headers)
    add = await async_client.post(
        f"/api/v1/fnb/checks/{cid}/items",
        json={"menu_item_id": menu_item["id"], "qty": 1},
        headers=frontdesk_headers,
    )
    assert add.status_code == 400


@pytest.mark.asyncio
async def test_rbac_housekeeping_denied(async_client, housekeeping_token, outlet):
    r = await async_client.post(
        "/api/v1/fnb/checks",
        json={"outlet_id": outlet["id"]},
        headers={"Authorization": f"Bearer {housekeeping_token}"},
    )
    assert r.status_code == 403
