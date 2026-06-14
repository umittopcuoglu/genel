"""CRM testleri: Guest 360, Segment, Campaign, Notes, Communication."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.front_office import Guest


@pytest.fixture
async def gold_guests(db: AsyncSession):
    """3 misafir oluştur — sonra segment kriterleri ile filtrelenecek."""
    guests = []
    for i in range(3):
        g = Guest(
            first_name=f"Vip{i}",
            last_name="Test",
            email=f"vip{i}@test.com",
            phone=f"+90555000111{i}",
            is_vip=(i == 0),
        )
        db.add(g)
        guests.append(g)
    await db.commit()
    for g in guests:
        await db.refresh(g)
    return guests


# ── Guest 360 ──

@pytest.mark.asyncio
async def test_guest_360_basic(async_client, guest_db, manager_headers):
    r = await async_client.get(f"/api/v1/crm/guests/{guest_db.id}/360", headers=manager_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["guest_id"] == str(guest_db.id)
    assert data["full_name"] == f"{guest_db.first_name} {guest_db.last_name}"
    assert data["total_stays"] >= 0
    assert "loyalty_tier" in data


@pytest.mark.asyncio
async def test_guest_360_not_found(async_client, manager_headers):
    fake = "00000000-0000-0000-0000-000000000000"
    r = await async_client.get(f"/api/v1/crm/guests/{fake}/360", headers=manager_headers)
    assert r.status_code == 404


# ── Segments ──

@pytest.mark.asyncio
async def test_create_and_list_segment(async_client, manager_headers):
    r = await async_client.post(
        "/api/v1/crm/segments",
        json={"name": "VIP Misafirler", "criteria": {"is_vip": True}},
        headers=manager_headers,
    )
    assert r.status_code == 201, r.text
    lst = await async_client.get("/api/v1/crm/segments", headers=manager_headers)
    assert lst.status_code == 200
    assert any(s["name"] == "VIP Misafirler" for s in lst.json())


@pytest.mark.asyncio
async def test_segment_preview_filters_vip(async_client, manager_headers, gold_guests):
    seg = await async_client.post(
        "/api/v1/crm/segments",
        json={"name": "Sadece VIP", "criteria": {"is_vip": True}},
        headers=manager_headers,
    )
    sid = seg.json()["id"]
    pv = await async_client.post(f"/api/v1/crm/segments/{sid}/preview", headers=manager_headers)
    assert pv.status_code == 200
    # 3 misafirden sadece 1 VIP
    assert pv.json()["match_count"] == 1


@pytest.mark.asyncio
async def test_segment_update(async_client, manager_headers):
    seg = await async_client.post(
        "/api/v1/crm/segments",
        json={"name": "Test Update", "criteria": {}},
        headers=manager_headers,
    )
    sid = seg.json()["id"]
    upd = await async_client.patch(
        f"/api/v1/crm/segments/{sid}",
        json={"is_active": False, "description": "kapalı"},
        headers=manager_headers,
    )
    assert upd.status_code == 200
    assert upd.json()["is_active"] is False


# ── Campaigns ──

@pytest.mark.asyncio
async def test_create_and_send_campaign(async_client, manager_headers, gold_guests):
    seg = await async_client.post(
        "/api/v1/crm/segments",
        json={"name": "Tüm Misafirler", "criteria": {}},
        headers=manager_headers,
    )
    sid = seg.json()["id"]
    cmp_ = await async_client.post(
        "/api/v1/crm/campaigns",
        json={
            "name": "Bahar İndirimi",
            "channel": "email",
            "subject": "Hoşgeldiniz",
            "body": "Sevgili misafirimiz, bahar indirimimizden faydalanın.",
            "segment_id": sid,
        },
        headers=manager_headers,
    )
    assert cmp_.status_code == 201
    cid = cmp_.json()["id"]
    sent = await async_client.post(f"/api/v1/crm/campaigns/{cid}/send", headers=manager_headers)
    assert sent.status_code == 200, sent.text
    body = sent.json()
    assert body["status"] == "sent"
    assert body["sent_count"] >= 3  # 3 misafire gönderildi


@pytest.mark.asyncio
async def test_campaign_double_send_blocked(async_client, manager_headers, gold_guests):
    seg = await async_client.post(
        "/api/v1/crm/segments", json={"name": "Tek Gönderim Segment", "criteria": {}}, headers=manager_headers
    )
    assert seg.status_code == 201, seg.text
    cmp_ = await async_client.post(
        "/api/v1/crm/campaigns",
        json={"name": "Tek Gönderim", "channel": "email", "body": "test", "segment_id": seg.json()["id"]},
        headers=manager_headers,
    )
    cid = cmp_.json()["id"]
    await async_client.post(f"/api/v1/crm/campaigns/{cid}/send", headers=manager_headers)
    second = await async_client.post(f"/api/v1/crm/campaigns/{cid}/send", headers=manager_headers)
    assert second.status_code == 400


# ── Notes ──

@pytest.mark.asyncio
async def test_guest_notes_create_and_list(async_client, frontdesk_headers, guest_db):
    cr = await async_client.post(
        "/api/v1/crm/notes",
        json={"guest_id": str(guest_db.id), "category": "allergy", "body": "Fıstık alerjisi", "is_pinned": True},
        headers=frontdesk_headers,
    )
    assert cr.status_code == 201, cr.text
    lst = await async_client.get(
        f"/api/v1/crm/guests/{guest_db.id}/notes", headers=frontdesk_headers
    )
    assert lst.status_code == 200
    rows = lst.json()
    assert len(rows) == 1
    assert rows[0]["category"] == "allergy"
    assert rows[0]["is_pinned"] is True


# ── Communication ──

@pytest.mark.asyncio
async def test_communication_log(async_client, frontdesk_headers, guest_db):
    cr = await async_client.post(
        "/api/v1/crm/communications",
        json={
            "guest_id": str(guest_db.id),
            "channel": "whatsapp",
            "direction": "outbound",
            "body": "Hoşgeldiniz",
        },
        headers=frontdesk_headers,
    )
    assert cr.status_code == 201, cr.text
    lst = await async_client.get(
        f"/api/v1/crm/guests/{guest_db.id}/communications", headers=frontdesk_headers
    )
    assert lst.status_code == 200
    assert len(lst.json()) == 1


# ── RBAC ──

@pytest.mark.asyncio
async def test_rbac_segment_create_denied_for_frontdesk(async_client, frontdesk_headers):
    r = await async_client.post(
        "/api/v1/crm/segments",
        json={"name": "X", "criteria": {}},
        headers=frontdesk_headers,
    )
    assert r.status_code == 403
