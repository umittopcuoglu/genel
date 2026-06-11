"""
Gece audit işlemleri: oda ücretlerini post etme, no-show işaretleme.
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_roles
from app.models.user import User
from app.models.finance import (
    Folio, FolioItem, NightAuditRun,
    FolioStatus, FolioItemType,
)
from app.models.front_office import (
    Reservation, Stay, Room,
    ReservationStatus, RoomStatus,
)
from app.schemas.finance import NightAuditRunRequest

router = APIRouter()


def err(code: str, msg: str, status_code: int = 400, details: dict = None):
    raise HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": msg, "details": details or {}}}
    )


@router.post("/night-audit/run", response_model=dict,
             summary="Gece audit çalıştır")
async def run_night_audit(
    data: NightAuditRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    business_date = data.business_date

    stmt = select(NightAuditRun).where(NightAuditRun.business_date == business_date)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        err("AUDIT_ALREADY_RUN", f"{business_date.isoformat()} için gece audit zaten çalıştırılmış",
            409, {"business_date": business_date.isoformat()})

    stats = {
        "rooms_posted": 0,
        "total_room_revenue": "0",
        "no_shows_marked": 0,
    }

    stmt_stays = select(Stay).options(
        selectinload(Stay.reservation),
        selectinload(Stay.room).selectinload(Room.room_type),
    ).where(
        Stay.is_checked_in.is_(True),
        Stay.is_checked_out.is_(False),
        Stay.deleted_at.is_(None),
        Stay.actual_check_in <= datetime.combine(business_date, datetime.max.time()).replace(tzinfo=timezone.utc),
    )
    result_stays = await db.execute(stmt_stays)
    active_stays = list(result_stays.scalars().all())

    rooms_posted = 0
    total_room_revenue = Decimal("0")

    for stay in active_stays:
        folio_stmt = select(Folio).where(
            Folio.reservation_id == stay.reservation_id,
            Folio.deleted_at.is_(None),
        )
        folio_result = await db.execute(folio_stmt)
        folio = folio_result.scalar_one_or_none()

        if not folio:
            folio = Folio(
                reservation_id=stay.reservation_id,
                guest_id=stay.guest_id,
                status=FolioStatus.OPEN.value,
                total=Decimal("0"),
                balance=Decimal("0"),
            )
            db.add(folio)
            await db.flush()
            await db.refresh(folio)

        rate = Decimal("0")
        if stay.reservation and stay.reservation.rate_plan_id:
            from app.models.reservation_ext import RatePlan
            rp_stmt = select(RatePlan).where(
                RatePlan.id == stay.reservation.rate_plan_id,
                RatePlan.deleted_at.is_(None),
            )
            rp_result = await db.execute(rp_stmt)
            rp = rp_result.scalar_one_or_none()
            if rp:
                rate = rp.base_rate
        elif stay.room and stay.room.room_type:
            rate = stay.room.room_type.default_rate

        if rate > 0:
            room_item = FolioItem(
                folio_id=folio.id,
                type=FolioItemType.ROOM.value,
                description=f"{business_date.isoformat()} gece oda ücreti",
                qty=1,
                unit_price=rate,
                tax_rate=Decimal("18"),
                posted_at=datetime.now(timezone.utc),
            )
            room_item.total = room_item.calculate_total()
            db.add(room_item)
            rooms_posted += 1
            total_room_revenue += room_item.total

    stats["rooms_posted"] = rooms_posted
    stats["total_room_revenue"] = str(total_room_revenue)

    no_show_stmt = select(Reservation).where(
        Reservation.check_in == business_date,
        Reservation.status == ReservationStatus.CONFIRMED.value,
        Reservation.deleted_at.is_(None),
    )
    no_show_result = await db.execute(no_show_stmt)
    no_show_reservations = list(no_show_result.scalars().all())

    no_shows_marked = 0
    for res in no_show_reservations:
        res.status = ReservationStatus.NO_SHOW.value
        res.no_show_marked_at = datetime.now(timezone.utc)
        if res.assigned_room_id:
            room_stmt = select(Room).where(Room.id == res.assigned_room_id)
            room_result = await db.execute(room_stmt)
            room = room_result.scalar_one_or_none()
            if room:
                room.status = RoomStatus.CLEAN.value
        no_shows_marked += 1

    stats["no_shows_marked"] = no_shows_marked

    for stay in active_stays:
        fl_stmt = select(Folio).where(
            Folio.reservation_id == stay.reservation_id,
            Folio.deleted_at.is_(None),
        )
        fl_result = await db.execute(fl_stmt)
        f = fl_result.scalar_one_or_none()
        if f:
            await db.refresh(f, ["items", "payments"])
            f.recalculate()

    audit_run = NightAuditRun(
        business_date=business_date,
        run_by=current_user.id,
        run_at=datetime.now(timezone.utc),
        stats=stats,
    )
    db.add(audit_run)
    await db.commit()
    await db.refresh(audit_run)

    return {
        "data": {
            "id": str(audit_run.id),
            "business_date": business_date.isoformat(),
            "run_by": str(audit_run.run_by),
            "run_at": audit_run.run_at.isoformat(),
            "stats": stats,
        },
        "meta": {},
    }
