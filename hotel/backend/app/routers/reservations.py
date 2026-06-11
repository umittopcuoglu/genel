"""
Rezervasyon CRUD + check-in/out + iptal endpointleri.
Müsaitlik kontrolü, rate_plan validasyonu, tarih çakışma yönetimi.
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_roles
from app.models.user import User
from app.models.front_office import RoomType, Guest, Reservation, Stay, Room
from app.models.reservation_ext import RatePlan, Availability
from app.schemas.front_office import (
    GuestCreate, GuestResponse,
    ReservationCreate as ResCreateSchema,
)
from app.schemas.reservation import (
    ReservationCreate, ReservationUpdate, ReservationResponse,
    CancelResponse, ReservationListResponse, ReservationListItem,
)

router = APIRouter()


async def get_fo_service(db: AsyncSession = Depends(get_db)):
    from app.services.front_office import FrontOfficeService
    return FrontOfficeService(db)


def err(code: str, msg: str, status: int = 400, details: dict = None):
    raise HTTPException(
        status_code=status,
        detail={"error": {"code": code, "message": msg, "details": details or {}}}
    )


def _calc_nights(check_in: date, check_out: date) -> int:
    return (check_out - check_in).days


async def _adjust_availability(
    db: AsyncSession,
    room_type_id: uuid.UUID,
    check_in: date,
    check_out: date,
    delta: int,  # +1 sold, -1 sold
):
    """Belirtilen tarih araliginda availability.sold_count'u delta kadar degistir."""
    stmt = select(Availability).where(
        Availability.room_type_id == room_type_id,
        Availability.date >= check_in,
        Availability.date < check_out,
        Availability.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    for row in rows:
        row.sold_count = max(0, row.sold_count + delta)


async def _check_availability(
    db: AsyncSession,
    room_type_id: uuid.UUID,
    check_in: date,
    check_out: date,
    exclude_reservation_id: Optional[uuid.UUID] = None,
) -> Optional[str]:
    """Her gece icin müsaitlik kontrolü. Hata varsa mesaj döndür."""
    stmt = select(Availability).where(
        Availability.room_type_id == room_type_id,
        Availability.date >= check_in,
        Availability.date < check_out,
        Availability.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    avail_rows = {r.date: r for r in result.scalars().all()}

    for i in range(_calc_nights(check_in, check_out)):
        d = date.fromordinal(check_in.toordinal() + i)
        if d in avail_rows:
            a = avail_rows[d]
            if a.sold_count >= a.available_count:
                return f"{d.isoformat()} tarihinde müsait oda yok"
    return None


@router.post("/reservations", response_model=ReservationResponse, status_code=201,
             summary="Yeni rezervasyon olustur")
async def create_reservation(
    data: ReservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    # 1. Tarih kontrolü
    today = date.today()
    if data.check_in < today:
        err("INVALID_DATE", "Gecmis tarih icin rezervasyon yapilamaz", 422)
    if data.check_in >= data.check_out:
        err("INVALID_DATE", "Cikis tarihi, giris tarihinden sonra olmalidir", 422)

    # 2. Guest bul veya olustur
    if data.guest_id:
        stmt = select(Guest).where(Guest.id == data.guest_id, Guest.deleted_at.is_(None))
        result = await db.execute(stmt)
        guest = result.scalar_one_or_none()
        if not guest:
            err("GUEST_NOT_FOUND", "Misafir bulunamadi", 404)
    elif data.guest:
        guest = Guest(
            first_name=data.guest.first_name,
            last_name=data.guest.last_name,
            email=data.guest.email,
            phone=data.guest.phone,
            nationality=data.guest.nationality,
        )
        db.add(guest)
        await db.flush()
        await db.refresh(guest)
    else:
        err("GUEST_REQUIRED", "Misafir bilgisi zorunludur", 422)

    # 3. Room type kontrolü
    rt_stmt = select(RoomType).where(RoomType.id == data.room_type_id, RoomType.deleted_at.is_(None))
    rt_result = await db.execute(rt_stmt)
    room_type = rt_result.scalar_one_or_none()
    if not room_type:
        err("ROOM_TYPE_NOT_FOUND", "Oda tipi bulunamadi", 404)

    # 4. Müsaitlik kontrolü
    avail_err = await _check_availability(db, data.room_type_id, data.check_in, data.check_out)
    if avail_err:
        err("NO_AVAILABILITY", f"Müsait oda yok: {avail_err}", 409)

    # 5. Rate plan kontrolü
    nights = _calc_nights(data.check_in, data.check_out)
    rate_value = room_type.default_rate
    if data.rate_plan_id:
        rp_stmt = select(RatePlan).where(
            RatePlan.id == data.rate_plan_id,
            RatePlan.room_type_id == data.room_type_id,
            RatePlan.deleted_at.is_(None),
        )
        rp_result = await db.execute(rp_stmt)
        rate_plan = rp_result.scalar_one_or_none()
        if not rate_plan:
            err("RATE_PLAN_NOT_FOUND", "Rate plan bulunamadi", 404)
        restrictions = rate_plan.restrictions or {}
        if restrictions.get("closed"):
            err("RATE_RESTRICTION", "Bu rate plan su anda kapali", 409)
        min_los = restrictions.get("min_los", 0)
        if min_los and nights < min_los:
            err("RATE_RESTRICTION", f"Minimum {min_los} gece gereklidir", 409)
        rate_value = rate_plan.base_rate

    # 6. Rezervasyon numarasi
    today_str = today.strftime("%Y%m%d")
    count_stmt = select(func.count()).select_from(Reservation).where(
        Reservation.reservation_number.like(f"RES-{today_str}-%")
    )
    count_result = await db.execute(count_stmt)
    seq = count_result.scalar_one() + 1

    total_amount = Decimal(str(nights)) * rate_value

    # 7. Olustur
    reservation = Reservation(
        reservation_number=f"RES-{today_str}-{seq:04d}",
        guest_id=guest.id,
        check_in=data.check_in,
        check_out=data.check_out,
        adults=data.adults or 1,
        children=data.children or 0,
        room_type_id=data.room_type_id,
        source=data.source or "direct",
        rate_plan_id=data.rate_plan_id,
        special_requests=data.special_requests,
        total_amount=total_amount,
        balance=total_amount,
        deposit_amount=Decimal("0"),
        deposit_paid=False,
    )
    db.add(reservation)

    # 8. Availability güncelle
    await _adjust_availability(db, data.room_type_id, data.check_in, data.check_out, 1)

    await db.commit()
    await db.refresh(reservation)

    # Reload with relations
    stmt = select(Reservation).options(
        selectinload(Reservation.guest),
        selectinload(Reservation.room_type),
    ).where(Reservation.id == reservation.id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/reservations", response_model=ReservationListResponse,
            summary="Rezervasyon listesi")
async def list_reservations(
    status: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    q: Optional[str] = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200, alias="per_page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    stmt = select(Reservation).options(
        selectinload(Reservation.guest),
        selectinload(Reservation.room_type),
    ).where(Reservation.deleted_at.is_(None))

    if status:
        stmt = stmt.where(Reservation.status == status)
    if from_date:
        stmt = stmt.where(Reservation.check_in >= from_date)
    if to_date:
        stmt = stmt.where(Reservation.check_out <= to_date)
    if q:
        stmt = stmt.where(
            or_(
                Reservation.reservation_number.ilike(f"%{q}%"),
                Reservation.guest.has(Guest.first_name.ilike(f"%{q}%")),
                Reservation.guest.has(Guest.last_name.ilike(f"%{q}%")),
            )
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = stmt.order_by(Reservation.check_in.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return ReservationListResponse(
        data=items,
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        }
    )


@router.get("/reservations/{reservation_id}", response_model=ReservationResponse,
            summary="Rezervasyon detayi")
async def get_reservation(
    reservation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    stmt = select(Reservation).options(
        selectinload(Reservation.guest),
        selectinload(Reservation.room_type),
        selectinload(Reservation.stays),
    ).where(Reservation.id == reservation_id, Reservation.deleted_at.is_(None))
    result = await db.execute(stmt)
    res = result.scalar_one_or_none()
    if not res:
        err("NOT_FOUND", "Rezervasyon bulunamadi", 404)
    return res


@router.put("/reservations/{reservation_id}", response_model=ReservationResponse,
            summary="Rezervasyon guncelle")
async def update_reservation(
    reservation_id: uuid.UUID,
    data: ReservationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    stmt = select(Reservation).options(
        selectinload(Reservation.guest),
        selectinload(Reservation.room_type),
    ).where(Reservation.id == reservation_id, Reservation.deleted_at.is_(None))
    result = await db.execute(stmt)
    res = result.scalar_one_or_none()
    if not res:
        err("NOT_FOUND", "Rezervasyon bulunamadi", 404)
    if res.status in ("checked_out", "cancelled"):
        err("RESERVATION_LOCKED", "Cikis yapilmis veya iptal edilmis rezervasyon degistirilemez", 409)

    old_check_in = res.check_in
    old_check_out = res.check_out
    old_room_type_id = res.room_type_id

    # Tarih ve oda tipi degisikliginde müsaitlik yeniden hesapla
    date_changed = (data.check_in and data.check_in != res.check_in) or (data.check_out and data.check_out != res.check_out)
    room_type_changed = data.room_type_id and data.room_type_id != res.room_type_id

    if data.check_in:
        res.check_in = data.check_in
    if data.check_out:
        res.check_out = data.check_out
    if data.adults is not None:
        res.adults = data.adults
    if data.children is not None:
        res.children = data.children
    if data.room_type_id:
        res.room_type_id = data.room_type_id
    if data.special_requests is not None:
        res.special_requests = data.special_requests

    # Müsaitlik güncellemesi
    if date_changed or room_type_changed:
        new_in = data.check_in or res.check_in
        new_out = data.check_out or res.check_out
        rt_id = data.room_type_id or old_room_type_id
        # Eski geceleri -1
        await _adjust_availability(db, old_room_type_id, old_check_in, old_check_out, -1)
        # Yeni geceleri kontrol et ve +1
        avail_err = await _check_availability(db, rt_id, new_in, new_out, exclude_reservation_id=reservation_id)
        if avail_err:
            # Rollback availability changes
            await _adjust_availability(db, old_room_type_id, old_check_in, old_check_out, 1)
            err("NO_AVAILABILITY", f"Yeni tarihte müsait oda yok: {avail_err}", 409)
        await _adjust_availability(db, rt_id, new_in, new_out, 1)

    await db.commit()
    await db.refresh(res)
    return res


@router.post("/reservations/{reservation_id}/cancel", response_model=ReservationResponse,
             summary="Rezervasyon iptal")
async def cancel_reservation(
    reservation_id: uuid.UUID,
    reason: str = Query(..., min_length=3),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    stmt = select(Reservation).options(
        selectinload(Reservation.guest),
        selectinload(Reservation.room_type),
    ).where(Reservation.id == reservation_id, Reservation.deleted_at.is_(None))
    result = await db.execute(stmt)
    res = result.scalar_one_or_none()
    if not res:
        err("NOT_FOUND", "Rezervasyon bulunamadi", 404)
    if res.status == "checked_in":
        err("RESERVATION_LOCKED", "Check-in yapilmis rezervasyon iptal edilemez", 409)

    res.status = "cancelled"
    res.cancellation_reason = reason
    res.cancelled_at = datetime.now(timezone.utc)

    # Availability: sold_count -1
    if res.room_type_id:
        await _adjust_availability(db, res.room_type_id, res.check_in, res.check_out, -1)

    await db.commit()
    await db.refresh(res)
    return res
