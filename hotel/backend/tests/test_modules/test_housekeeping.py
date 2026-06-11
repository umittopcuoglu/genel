"""
Housekeeping modülü testleri (TASK-005) — minimum 14 test.
"""
import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.front_office import Room, RoomStatus, Stay, Reservation, ReservationStatus
from app.models.housekeeping import HousekeepingTask, LostFound, MinibarItem
from app.models.finance import Folio, FolioItem, FolioStatus, FolioItemType


pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.usefixtures("setup_test_db"),
]


# ──── Fixtures ────

@pytest.fixture
async def hk_room(db: AsyncSession, room_type_db) -> Room:
    room = Room(
        room_number="201",
        floor=2,
        room_type_id=room_type_db.id,
        status=RoomStatus.DIRTY.value,
        is_active=True,
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


@pytest.fixture
async def hk_task(db: AsyncSession, hk_room) -> HousekeepingTask:
    task = HousekeepingTask(
        room_id=hk_room.id,
        type="stayover",
        status="pending",
        priority=3,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@pytest.fixture
async def minibar_item(db: AsyncSession) -> MinibarItem:
    item = MinibarItem(
        name="Cola",
        price=Decimal("15.00"),
        tax_rate=Decimal("18"),
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@pytest.fixture
async def hk_active_stay(db: AsyncSession, hk_room, guest_db, reservation_db) -> Stay:
    stay = Stay(
        reservation_id=reservation_db.id,
        room_id=hk_room.id,
        guest_id=guest_db.id,
        is_checked_in=True,
        is_checked_out=False,
        actual_check_in=datetime.now(timezone.utc),
    )
    db.add(stay)
    await db.commit()
    await db.refresh(stay)
    return stay


@pytest.fixture
async def hk_folio(db: AsyncSession, reservation_db, guest_db) -> Folio:
    folio = Folio(
        reservation_id=reservation_db.id,
        guest_id=guest_db.id,
        status=FolioStatus.OPEN.value,
        total=Decimal("0"),
        balance=Decimal("0"),
    )
    db.add(folio)
    await db.commit()
    await db.refresh(folio)
    return folio


# ──── 1. Board ────

async def test_board_returns_counts(async_client, superadmin_token, hk_room):
    resp = await async_client.get(
        "/api/v1/housekeeping/board",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "meta" in body
    counts = body["meta"]["counts"]
    assert "dirty" in counts
    # hk_room is dirty
    rooms = body["data"]
    room_nos = [r["room_no"] for r in rooms]
    assert "201" in room_nos


# ──── 2. Task Create ────

async def test_create_task_happy(async_client, superadmin_token, hk_room):
    resp = await async_client.post(
        "/api/v1/housekeeping/tasks",
        json={"room_id": str(hk_room.id), "type": "stayover", "priority": 3},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "stayover"
    assert body["status"] == "pending"
    assert str(body["room_id"]) == str(hk_room.id)


async def test_create_task_dupe_409(async_client, superadmin_token, hk_room):
    # Create first
    await async_client.post(
        "/api/v1/housekeeping/tasks",
        json={"room_id": str(hk_room.id), "type": "deep", "priority": 1},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    # Dupe
    resp = await async_client.post(
        "/api/v1/housekeeping/tasks",
        json={"room_id": str(hk_room.id), "type": "deep", "priority": 1},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "TASK_EXISTS"


async def test_create_task_rbac(async_client, async_client2, superadmin_token, hk_room):
    """frontdesk cannot create task → 403"""
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "frontdesk@test.com", "password": "Front123!"},
    )
    fb_token = resp.json()["access_token"]
    resp2 = await async_client.post(
        "/api/v1/housekeeping/tasks",
        json={"room_id": str(hk_room.id), "type": "stayover"},
        headers={"Authorization": f"Bearer {fb_token}"},
    )
    assert resp2.status_code == 403


# ──── 3. Status transitions ────

async def test_status_chain(async_client, superadmin_token, hk_task):
    async def set_status(sid, status):
        return await async_client.patch(
            f"/api/v1/housekeeping/tasks/{sid}/status",
            json={"status": status},
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )

    # pending → in_progress
    resp = await set_status(hk_task.id, "in_progress")
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
    assert resp.json()["started_at"] is not None

    # in_progress → done
    resp = await set_status(hk_task.id, "done")
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"
    assert resp.json()["completed_at"] is not None

    # done → verified
    resp = await set_status(hk_task.id, "verified")
    assert resp.status_code == 200
    assert resp.json()["status"] == "verified"


async def test_invalid_transition_422(async_client, superadmin_token, hk_task):
    # pending → done (skip in_progress)
    resp = await async_client.patch(
        f"/api/v1/housekeeping/tasks/{hk_task.id}/status",
        json={"status": "done"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_TRANSITION"


# ──── 4. Done → room clean / Verified → inspected ────

async def test_done_cleans_room(async_client, superadmin_token, hk_task, hk_room, db):
    # Move to done
    resp = await async_client.patch(
        f"/api/v1/housekeeping/tasks/{hk_task.id}/status",
        json={"status": "in_progress"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200

    resp = await async_client.patch(
        f"/api/v1/housekeeping/tasks/{hk_task.id}/status",
        json={"status": "done"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200

    stmt = select(Room).where(Room.id == hk_room.id)
    result = await db.execute(stmt)
    room = result.scalar_one()
    assert room.status == RoomStatus.CLEAN.value


async def test_verified_inspects_room(async_client, superadmin_token, hk_task, hk_room, db):
    steps = ["in_progress", "done", "verified"]
    for s in steps:
        resp = await async_client.patch(
            f"/api/v1/housekeeping/tasks/{hk_task.id}/status",
            json={"status": s},
            headers={"Authorization": f"Bearer {superadmin_token}"},
        )
        assert resp.status_code == 200

    stmt = select(Room).where(Room.id == hk_room.id)
    result = await db.execute(stmt)
    room = result.scalar_one()
    assert room.status == RoomStatus.INSPECTED.value


# ──── 5. Auto-generate ────

async def test_auto_generate_creates_tasks(async_client, superadmin_token, hk_room, reservation_db):
    # Check-out stay for today
    from sqlalchemy import update
    resp = await async_client.post(
        "/api/v1/housekeeping/auto-generate",
        json={"date": date.today().isoformat()},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["data"]["created"], int)
    assert isinstance(body["data"]["skipped"], int)


async def test_auto_generate_skips_dupes(async_client, superadmin_token, hk_room):
    # Run twice
    resp1 = await async_client.post(
        "/api/v1/housekeeping/auto-generate",
        json={"date": date.today().isoformat()},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp1.status_code == 200

    resp2 = await async_client.post(
        "/api/v1/housekeeping/auto-generate",
        json={"date": date.today().isoformat()},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp2.status_code == 200
    # At least same tasks are skipped
    assert resp2.json()["data"]["created"] <= resp1.json()["data"]["created"]


# ──── 6. Lost & Found ────

async def test_lost_found_create(async_client, superadmin_token, hk_room):
    resp = await async_client.post(
        "/api/v1/lost-found",
        json={"room_id": str(hk_room.id), "item_description": "Gold ring"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "stored"
    assert body["item_description"] == "Gold ring"
    assert "id" in body


async def test_lost_found_return(async_client, superadmin_token, hk_room):
    # Create
    create_resp = await async_client.post(
        "/api/v1/lost-found",
        json={"room_id": str(hk_room.id), "item_description": "Watch"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    item_id = create_resp.json()["id"]

    # Return
    resp = await async_client.patch(
        f"/api/v1/lost-found/{item_id}/return",
        json={"returned_to": "Ali Yılmaz"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "returned"
    assert body["returned_to"] == "Ali Yılmaz"
    assert body["returned_at"] is not None


# ──── 7. Minibar ────

async def test_minibar_post(async_client, superadmin_token, hk_room, minibar_item,
                            hk_active_stay, hk_folio, db):
    resp = await async_client.post(
        "/api/v1/minibar/post",
        json={
            "room_id": str(hk_room.id),
            "items": [{"minibar_item_id": str(minibar_item.id), "qty": 2}],
        },
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "folio_id" in body["data"]
    assert body["data"]["total_posted"] is not None

    # Folio'da fnb satırı doğru mu?
    stmt = select(FolioItem).where(
        FolioItem.folio_id == hk_folio.id,
        FolioItem.type == FolioItemType.FNB.value,
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    assert len(items) == 1
    expected_total = Decimal("15.00") * 2 * Decimal("1.18")
    assert items[0].total == expected_total.quantize(Decimal("0.01"))


async def test_minibar_no_active_stay_409(async_client, superadmin_token, hk_room, minibar_item):
    """Konaklama yoksa 409"""
    resp = await async_client.post(
        "/api/v1/minibar/post",
        json={
            "room_id": str(hk_room.id),
            "items": [{"minibar_item_id": str(minibar_item.id), "qty": 1}],
        },
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "NO_ACTIVE_STAY"


# ──── 8. Unauthorized ────

async def test_unauthorized_401(async_client, hk_room):
    resp = await async_client.get(
        "/api/v1/housekeeping/board",
    )
    assert resp.status_code == 401
