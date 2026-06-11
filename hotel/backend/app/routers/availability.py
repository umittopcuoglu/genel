"""
Availability calendar ve occupancy endpointleri.
"""
import uuid
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_roles
from app.models.user import User
from app.models.front_office import RoomType, Room
from app.models.reservation_ext import Availability

router = APIRouter()


def err(code: str, msg: str, status: int = 400, details: dict = None):
    raise HTTPException(
        status_code=status,
        detail={"error": {"code": code, "message": msg, "details": details or {}}}
    )


@router.get("/availability/calendar",
            summary="Müsaitlik takvimi")
async def get_availability_calendar(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    if from_date >= to_date:
        err("INVALID_DATE", "Bitis tarihi baslangictan sonra olmalidir", 422)
    if (to_date - from_date).days > 365:
        err("RANGE_TOO_LARGE", "En fazla 365 gun sorgulanabilir", 422)

    # Tüm oda tiplerini getir
    rt_stmt = select(RoomType).where(RoomType.deleted_at.is_(None), RoomType.is_active.is_(True))
    rt_result = await db.execute(rt_stmt)
    room_types = list(rt_result.scalars().all())

    # Tüm availability kayitlari
    av_stmt = select(Availability).where(
        Availability.room_type_id.in_([rt.id for rt in room_types]),
        Availability.date >= from_date,
        Availability.date < to_date,
        Availability.deleted_at.is_(None),
    )
    av_result = await db.execute(av_stmt)
    avail_rows = list(av_result.scalars().all())

    avail_map = {}
    for a in avail_rows:
        avail_map[(a.room_type_id, a.date)] = a

    data = []
    for rt in room_types:
        days = []
        for i in range((to_date - from_date).days):
            d = date.fromordinal(from_date.toordinal() + i)
            a = avail_map.get((rt.id, d))
            days.append({
                "date": d.isoformat(),
                "available": a.available_count if a else 0,
                "sold": a.sold_count if a else 0,
            })
        data.append({
            "room_type": {"id": str(rt.id), "code": rt.code, "name": rt.name},
            "days": days,
        })

    return {"data": data, "meta": {}}


@router.get("/occupancy",
            summary="Doluluk yuzdesi")
async def get_occupancy(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    if from_date >= to_date:
        err("INVALID_DATE", "Bitis tarihi baslangictan sonra olmalidir", 422)

    # Toplam oda sayisi
    room_stmt = select(func.count()).select_from(Room).where(
        Room.deleted_at.is_(None), Room.is_active.is_(True)
    )
    room_result = await db.execute(room_stmt)
    total_rooms = room_result.scalar_one()
    if total_rooms == 0:
        return {"data": [], "meta": {}}

    data = []
    for i in range((to_date - from_date).days):
        d = date.fromordinal(from_date.toordinal() + i)
        # Sold count sum on that day
        av_stmt = select(func.coalesce(func.sum(Availability.sold_count), 0)).where(
            Availability.date == d,
            Availability.deleted_at.is_(None),
        )
        av_result = await db.execute(av_stmt)
        sold = av_result.scalar_one()
        occupancy_pct = round((sold / total_rooms) * 100, 1) if total_rooms else 0
        data.append({
            "date": d.isoformat(),
            "occupancy_pct": occupancy_pct,
            "sold": sold,
            "capacity": total_rooms,
        })

    return {"data": data, "meta": {}}
