"""
Housekeeping router: görev panosu + CRUD + durum geçişleri + auto-generate.
"""
import uuid
from datetime import date, datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload, joinedload

from app.core.db import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_roles
from app.models.user import User
from app.models.front_office import Room, Stay, Reservation, ReservationStatus, RoomStatus
from app.models.housekeeping import HousekeepingTask, LostFound
from app.schemas.housekeeping import (
    RoomBoardResponse, RoomBoardItem, RoomBoardCounts,
    HousekeepingTaskCreate, HousekeepingTaskStatusUpdate,
    HousekeepingTaskResponse, AutoGenerateRequest, AutoGenerateResponse,
)

router = APIRouter()

VALID_TRANSITIONS = {
    "pending": ["in_progress"],
    "in_progress": ["done"],
    "done": ["verified"],
}


def err(code: str, msg: str, status_code: int = 400, details: dict = None):
    raise HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": msg, "details": details or {}}}
    )


# ──── Board ────

@router.get("/housekeeping/board", response_model=RoomBoardResponse,
            summary="Oda durum panosu")
async def get_housekeeping_board(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping", "frontdesk"])),
):
    stmt = select(Room).options(
        joinedload(Room.room_type),
    ).where(Room.deleted_at.is_(None), Room.is_active.is_(True)).order_by(Room.floor, Room.room_number)
    result = await db.execute(stmt)
    rooms = list(result.unique().scalars().all())

    # Aktif görevleri topla
    task_stmt = select(HousekeepingTask).where(
        HousekeepingTask.deleted_at.is_(None),
        HousekeepingTask.status.in_(["pending", "in_progress"]),
    )
    task_result = await db.execute(task_stmt)
    active_tasks = list(task_result.scalars().all())
    task_map = {str(t.room_id): t for t in active_tasks}

    # O gün aktif stay'leri bul
    today = date.today()
    day_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    stay_stmt = select(Stay).where(
        Stay.is_checked_in.is_(True),
        Stay.is_checked_out.is_(False),
        Stay.deleted_at.is_(None),
    )
    stay_result = await db.execute(stay_stmt)
    active_room_ids = set(str(s.room_id) for s in stay_result.scalars().all())

    counts = {"clean": 0, "dirty": 0, "inspected": 0, "out_of_order": 0}
    board_items = []

    for room in rooms:
        status_key = room.status or "dirty"
        if status_key in counts:
            counts[status_key] += 1
        else:
            counts["dirty"] += 1

        task = task_map.get(str(room.id))
        task_data = None
        if task:
            task_data = {
                "id": str(task.id),
                "type": task.type,
                "status": task.status,
                "priority": task.priority,
            }

        board_items.append(RoomBoardItem(
            room_no=room.room_number,
            floor=room.floor,
            room_type=room.room_type.name if room.room_type else "",
            status=status_key,
            active_task=task_data,
            current_guest=str(room.id) in active_room_ids,
        ))

    return RoomBoardResponse(
        data=board_items,
        meta={"counts": counts}
    )


# ──── Tasks ────

@router.post("/housekeeping/tasks", response_model=HousekeepingTaskResponse,
             status_code=201, summary="Temizlik görevi oluştur")
async def create_task(
    data: HousekeepingTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping"])),
):
    # Dupe kontrolü
    stmt = select(HousekeepingTask).where(
        HousekeepingTask.room_id == data.room_id,
        HousekeepingTask.type == data.type,
        HousekeepingTask.status.in_(["pending", "in_progress"]),
        HousekeepingTask.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        err("TASK_EXISTS", f"Aynı odada ({data.room_id}) '{data.type}' tipinde açık görev var", 409)

    task = HousekeepingTask(
        room_id=data.room_id,
        assigned_to=data.assigned_to,
        type=data.type,
        priority=data.priority,
        notes=data.notes,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/housekeeping/tasks/{task_id}/status", response_model=HousekeepingTaskResponse,
              summary="Görev durumu güncelle")
async def update_task_status(
    task_id: uuid.UUID,
    data: HousekeepingTaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping"])),
):
    stmt = select(HousekeepingTask).options(
        joinedload(HousekeepingTask.room),
    ).where(HousekeepingTask.id == task_id, HousekeepingTask.deleted_at.is_(None))
    result = await db.execute(stmt)
    task = result.unique().scalar_one_or_none()
    if not task:
        err("NOT_FOUND", "Görev bulunamadı", 404)

    new_status = data.status
    allowed = VALID_TRANSITIONS.get(task.status, [])
    if new_status not in allowed:
        err("INVALID_TRANSITION",
            f"'{task.status}' → '{new_status}' geçersiz. İzin verilenler: {allowed}",
            422)

    task.status = new_status
    now = datetime.now(timezone.utc)

    if new_status == "in_progress":
        task.started_at = now
    elif new_status == "done":
        task.completed_at = now
        # Room status → clean
        room_stmt = select(Room).where(Room.id == task.room_id)
        room_result = await db.execute(room_stmt)
        room = room_result.scalar_one_or_none()
        if room:
            room.status = RoomStatus.CLEAN.value
    elif new_status == "verified":
        # Room status → inspected
        room_stmt = select(Room).where(Room.id == task.room_id)
        room_result = await db.execute(room_stmt)
        room = room_result.scalar_one_or_none()
        if room:
            room.status = RoomStatus.INSPECTED.value

    await db.commit()
    await db.refresh(task)
    return task


# ──── Auto-generate ────

@router.post("/housekeeping/auto-generate", response_model=AutoGenerateResponse,
             summary="Günlük görevleri otomatik oluştur")
async def auto_generate_tasks(
    data: AutoGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    target = data.date
    created = 0
    skipped = 0

    # 1. Bugün checkout yapan odalar → checkout görevi
    day_end = datetime.combine(target, datetime.max.time()).replace(tzinfo=timezone.utc)
    checkout_stmt = select(Stay).where(
        Stay.is_checked_out.is_(True),
        Stay.deleted_at.is_(None),
        Stay.actual_check_out >= datetime.combine(target, datetime.min.time()).replace(tzinfo=timezone.utc),
        Stay.actual_check_out <= day_end,
    )
    checkout_result = await db.execute(checkout_stmt)
    checkout_stays = list(checkout_result.scalars().all())

    checkout_room_ids = set()
    for stay in checkout_stays:
        if stay.room_id:
            checkout_room_ids.add(stay.room_id)

    for room_id in checkout_room_ids:
        dupe = await _check_dupe_task(db, room_id, "checkout")
        if dupe:
            skipped += 1
            continue
        db.add(HousekeepingTask(room_id=room_id, type="checkout", priority=2))
        created += 1

    # 2. In-house odalar → stayover görevi
    in_house_stmt = select(Stay).where(
        Stay.is_checked_in.is_(True),
        Stay.is_checked_out.is_(False),
        Stay.deleted_at.is_(None),
    )
    in_house_result = await db.execute(in_house_stmt)
    in_house_stays = list(in_house_result.scalars().all())

    stayover_room_ids = set()
    for stay in in_house_stays:
        if stay.room_id:
            stayover_room_ids.add(stay.room_id)

    for room_id in stayover_room_ids:
        dupe = await _check_dupe_task(db, room_id, "stayover")
        if dupe:
            skipped += 1
            continue
        db.add(HousekeepingTask(room_id=room_id, type="stayover", priority=3))
        created += 1

    await db.commit()

    return AutoGenerateResponse(
        data={"created": created, "skipped": skipped},
        meta={}
    )


async def _check_dupe_task(db: AsyncSession, room_id: uuid.UUID, task_type: str) -> bool:
    stmt = select(HousekeepingTask).where(
        HousekeepingTask.room_id == room_id,
        HousekeepingTask.type == task_type,
        HousekeepingTask.status.in_(["pending", "in_progress", "done"]),
        HousekeepingTask.deleted_at.is_(None),
    )
    # Only today's tasks
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    stmt = stmt.where(HousekeepingTask.created_at >= today_start)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None
