"""
Rapor endpoint'leri: doluluk, ADR, RevPAR.
"""
from datetime import date, datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_roles
from app.models.user import User
from app.models.front_office import Stay, Room
from app.models.finance import Folio, FolioItem, FolioItemType
from app.schemas.finance import OccupancyReport, ADRReport, RevPARReport

router = APIRouter()


def err(code: str, msg: str, status_code: int = 400, details: dict = None):
    raise HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": msg, "details": details or {}}}
    )


async def _get_total_rooms(db: AsyncSession) -> int:
    stmt = select(func.count()).select_from(Room).where(
        Room.deleted_at.is_(None),
        Room.is_active.is_(True),
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/reports/occupancy", response_model=OccupancyReport,
            summary="Günlük doluluk raporu")
async def occupancy_report(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "accounting"])),
):
    if from_date > to_date:
        err("INVALID_DATE", "Başlangıç tarihi bitiş tarihinden sonra olamaz", 422)

    total_rooms = await _get_total_rooms(db)

    rows = []
    current = from_date
    while current <= to_date:
        day_end = datetime.combine(current, datetime.max.time()).replace(tzinfo=timezone.utc)
        stmt = select(func.count()).select_from(Stay).where(
            Stay.is_checked_in.is_(True),
            Stay.is_checked_out.is_(False),
            Stay.deleted_at.is_(None),
            Stay.actual_check_in <= day_end,
            (Stay.actual_check_out.is_(None) | (Stay.actual_check_out > day_end)),
        )
        result = await db.execute(stmt)
        occupied = result.scalar_one()

        rate = round(occupied / total_rooms * 100, 2) if total_rooms > 0 else 0.0
        rows.append({
            "date": current,
            "total_rooms": total_rooms,
            "occupied_rooms": occupied,
            "occupancy_rate": rate,
        })
        current = date.fromordinal(current.toordinal() + 1)

    summary = {
        "avg_occupancy": round(
            sum(r["occupancy_rate"] for r in rows) / len(rows), 2
        ) if rows else 0.0,
        "total_occupied_room_nights": sum(r["occupied_rooms"] for r in rows),
    }

    return OccupancyReport(data=rows, meta={"summary": summary})


@router.get("/reports/adr", response_model=ADRReport,
            summary="ADR (Average Daily Rate) raporu")
async def adr_report(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "accounting"])),
):
    if from_date > to_date:
        err("INVALID_DATE", "Başlangıç tarihi bitiş tarihinden sonra olamaz", 422)

    rows = []
    current = from_date
    while current <= to_date:
        day_start = datetime.combine(current, datetime.min.time()).replace(tzinfo=timezone.utc)
        day_end = datetime.combine(current, datetime.max.time()).replace(tzinfo=timezone.utc)

        stmt = select(
            func.coalesce(func.sum(FolioItem.total), 0)
        ).select_from(FolioItem).join(
            Folio, FolioItem.folio_id == Folio.id
        ).where(
            FolioItem.type == FolioItemType.ROOM.value,
            FolioItem.deleted_at.is_(None),
            FolioItem.posted_at >= day_start,
            FolioItem.posted_at <= day_end,
        )
        result = await db.execute(stmt)
        room_revenue = result.scalar_one() or Decimal("0")

        sold_stmt = select(func.count()).select_from(Stay).where(
            Stay.is_checked_in.is_(True),
            Stay.deleted_at.is_(None),
            Stay.actual_check_in <= day_end,
            (Stay.actual_check_out.is_(None) | (Stay.actual_check_out > day_end)),
        )
        sold_result = await db.execute(sold_stmt)
        sold_rooms = sold_result.scalar_one()

        adr = round(room_revenue / sold_rooms, 2) if sold_rooms > 0 else Decimal("0")
        rows.append({
            "date": current,
            "room_revenue": room_revenue,
            "sold_rooms": sold_rooms,
            "adr": adr,
        })
        current = date.fromordinal(current.toordinal() + 1)

    total_revenue = sum(r["room_revenue"] for r in rows)
    total_sold = sum(r["sold_rooms"] for r in rows)
    summary = {
        "avg_adr": round(total_revenue / total_sold, 2) if total_sold > 0 else Decimal("0"),
        "total_room_revenue": total_revenue,
        "total_sold_rooms": total_sold,
    }

    return ADRReport(data=rows, meta={"summary": summary})


@router.get("/reports/revpar", response_model=RevPARReport,
            summary="RevPAR (Revenue Per Available Room) raporu")
async def revpar_report(
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "accounting"])),
):
    if from_date > to_date:
        err("INVALID_DATE", "Başlangıç tarihi bitiş tarihinden sonra olamaz", 422)

    total_rooms = await _get_total_rooms(db)

    rows = []
    current = from_date
    while current <= to_date:
        day_start = datetime.combine(current, datetime.min.time()).replace(tzinfo=timezone.utc)
        day_end = datetime.combine(current, datetime.max.time()).replace(tzinfo=timezone.utc)

        stmt = select(
            func.coalesce(func.sum(FolioItem.total), 0)
        ).select_from(FolioItem).join(
            Folio, FolioItem.folio_id == Folio.id
        ).where(
            FolioItem.type == FolioItemType.ROOM.value,
            FolioItem.deleted_at.is_(None),
            FolioItem.posted_at >= day_start,
            FolioItem.posted_at <= day_end,
        )
        result = await db.execute(stmt)
        room_revenue = result.scalar_one() or Decimal("0")

        revpar = round(room_revenue / total_rooms, 2) if total_rooms > 0 else Decimal("0")
        rows.append({
            "date": current,
            "room_revenue": room_revenue,
            "total_rooms": total_rooms,
            "revpar": revpar,
        })
        current = date.fromordinal(current.toordinal() + 1)

    total_revenue = sum(r["room_revenue"] for r in rows)
    summary = {
        "avg_revpar": round(total_revenue / (total_rooms * len(rows)), 2) if total_rooms > 0 else Decimal("0"),
        "total_room_revenue": total_revenue,
        "total_available_room_nights": total_rooms * len(rows),
    }

    return RevPARReport(data=rows, meta={"summary": summary})
