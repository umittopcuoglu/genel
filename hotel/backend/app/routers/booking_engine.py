"""
Booking Engine — otelin KOMİSYONSUZ doğrudan satış kanalı (public API).

Misafir, otel web sitesinden kimlik doğrulamasız:
  1. Müsaitlik arar      → GET  /api/v1/public/availability
  2. Rezervasyon yapar   → POST /api/v1/public/bookings
  3. Onayını sorgular    → GET  /api/v1/public/bookings/{number}

Her rezervasyonda stok düşer ve Channel Manager tüm aktif OTA'lara
yeni envanteri push eder (overbooking koruması).
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.front_office import Guest, Reservation, ReservationSource, RoomType
from app.models.reservation_ext import Availability
from app.services.channel_sync_service import ChannelSyncService

router = APIRouter(prefix="/api/v1/public", tags=["Booking Engine (Public)"])

MAX_NIGHTS = 30


def err(code: str, msg: str, status: int = 400):
    raise HTTPException(status_code=status, detail={"error": {"code": code, "message": msg, "details": {}}})


# ── Şemalar ──

class AvailableRoomType(BaseModel):
    room_type_id: uuid.UUID
    code: str
    name: str
    description: Optional[str] = None
    max_guests: int
    nightly_rate: Decimal
    total_price: Decimal
    nights: int
    rooms_left: int


class PublicBookingCreate(BaseModel):
    room_type_id: uuid.UUID
    check_in: date
    check_out: date
    adults: int = Field(1, ge=1, le=10)
    children: int = Field(0, ge=0, le=10)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=30)
    special_requests: Optional[str] = Field(None, max_length=1000)


class PublicBookingResponse(BaseModel):
    reservation_number: str
    status: str
    room_type_name: str
    check_in: date
    check_out: date
    nights: int
    total_amount: Decimal
    guest_name: str
    channels_notified: int


# ── Yardımcılar ──

def _nights(check_in: date, check_out: date) -> int:
    return (check_out - check_in).days


def _validate_dates(check_in: date, check_out: date) -> None:
    if check_in < date.today():
        err("INVALID_DATE", "Geçmiş tarih için arama/rezervasyon yapılamaz.", 422)
    if check_in >= check_out:
        err("INVALID_DATE", "Çıkış tarihi girişten sonra olmalıdır.", 422)
    if _nights(check_in, check_out) > MAX_NIGHTS:
        err("INVALID_DATE", f"En fazla {MAX_NIGHTS} gece için rezervasyon yapılabilir.", 422)


async def _rooms_left(db: AsyncSession, room_type_id: uuid.UUID, check_in: date, check_out: date) -> int:
    """Aralıktaki en kısıtlı gecenin kalan oda sayısı (envanter tanımsızsa 0)."""
    q = select(Availability).where(
        Availability.room_type_id == room_type_id,
        Availability.date >= check_in,
        Availability.date < check_out,
        Availability.deleted_at.is_(None),
    )
    rows = {r.date: r for r in (await db.execute(q)).scalars().all()}
    left = None
    for i in range(_nights(check_in, check_out)):
        d = date.fromordinal(check_in.toordinal() + i)
        row = rows.get(d)
        night_left = max(0, row.available_count - row.sold_count) if row else 0
        left = night_left if left is None else min(left, night_left)
    return left or 0


# ── Endpoint'ler ──

@router.get("/availability", response_model=list[AvailableRoomType], summary="Müsait oda tiplerini ara")
async def search_availability(
    check_in: date = Query(...),
    check_out: date = Query(...),
    adults: int = Query(1, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    _validate_dates(check_in, check_out)
    nights = _nights(check_in, check_out)

    q = select(RoomType).where(RoomType.is_active.is_(True), RoomType.deleted_at.is_(None))
    room_types = (await db.execute(q)).scalars().all()

    results: list[AvailableRoomType] = []
    for rt in room_types:
        if rt.max_guests < adults:
            continue
        left = await _rooms_left(db, rt.id, check_in, check_out)
        if left <= 0:
            continue
        rate = rt.default_rate or Decimal("0")
        results.append(
            AvailableRoomType(
                room_type_id=rt.id,
                code=rt.code,
                name=rt.name,
                description=rt.description,
                max_guests=rt.max_guests,
                nightly_rate=rate,
                total_price=rate * nights,
                nights=nights,
                rooms_left=left,
            )
        )
    results.sort(key=lambda r: r.nightly_rate)
    return results


@router.post("/bookings", response_model=PublicBookingResponse, status_code=201, summary="Doğrudan rezervasyon oluştur")
async def create_public_booking(data: PublicBookingCreate, db: AsyncSession = Depends(get_db)):
    _validate_dates(data.check_in, data.check_out)

    rt = (
        await db.execute(
            select(RoomType).where(
                RoomType.id == data.room_type_id,
                RoomType.is_active.is_(True),
                RoomType.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if not rt:
        err("ROOM_TYPE_NOT_FOUND", "Oda tipi bulunamadı.", 404)
    if rt.max_guests < data.adults:
        err("CAPACITY_EXCEEDED", f"Bu oda tipi en fazla {rt.max_guests} yetişkin alır.", 422)

    # Müsaitlik — son odayı iki kanalın aynı anda satmasını engelle
    left = await _rooms_left(db, rt.id, data.check_in, data.check_out)
    if left <= 0:
        err("NO_AVAILABILITY", "Seçilen tarihlerde müsait oda kalmadı.", 409)

    # Misafir: e-postayla eşleşen kayıt varsa kullan, yoksa oluştur
    guest = (
        await db.execute(
            select(Guest).where(Guest.email == data.email, Guest.deleted_at.is_(None))
        )
    ).scalars().first()
    if not guest:
        guest = Guest(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
        )
        db.add(guest)
        await db.flush()

    nights = _nights(data.check_in, data.check_out)
    rate = rt.default_rate or Decimal("0")
    total = rate * nights

    today_str = date.today().strftime("%Y%m%d")
    seq = (
        await db.execute(
            select(func.count()).select_from(Reservation).where(
                Reservation.reservation_number.like(f"WEB-{today_str}-%")
            )
        )
    ).scalar_one() + 1

    reservation = Reservation(
        reservation_number=f"WEB-{today_str}-{seq:04d}",
        guest_id=guest.id,
        check_in=data.check_in,
        check_out=data.check_out,
        adults=data.adults,
        children=data.children,
        room_type_id=rt.id,
        source=ReservationSource.DIRECT,  # web booking engine = komisyonsuz doğrudan kanal
        special_requests=data.special_requests,
        total_amount=total,
        balance=total,
        deposit_amount=Decimal("0"),
        deposit_paid=False,
    )
    db.add(reservation)

    # Stok düş
    avail_rows = (
        await db.execute(
            select(Availability).where(
                Availability.room_type_id == rt.id,
                Availability.date >= data.check_in,
                Availability.date < data.check_out,
                Availability.deleted_at.is_(None),
            )
        )
    ).scalars().all()
    for row in avail_rows:
        row.sold_count = row.sold_count + 1

    # Channel Manager: tüm aktif kanallara yeni envanteri push et (aynı transaction)
    sync = await ChannelSyncService.push_inventory_update(
        db, rt.id, data.check_in, data.check_out, trigger="reservation"
    )

    # Yanıt değerlerini commit'ten önce yakala (expire/refresh gerektirmez)
    response = PublicBookingResponse(
        reservation_number=reservation.reservation_number,
        status="confirmed",
        room_type_name=rt.name,
        check_in=data.check_in,
        check_out=data.check_out,
        nights=nights,
        total_amount=total,
        guest_name=f"{guest.first_name} {guest.last_name}",
        channels_notified=sync["channels_notified"],
    )
    await db.commit()
    return response


@router.get("/bookings/{reservation_number}", response_model=PublicBookingResponse, summary="Rezervasyon onayı sorgula")
async def get_public_booking(
    reservation_number: str,
    email: EmailStr = Query(..., description="Rezervasyondaki misafir e-postası (doğrulama)"),
    db: AsyncSession = Depends(get_db),
):
    res = (
        await db.execute(
            select(Reservation).where(
                Reservation.reservation_number == reservation_number,
                Reservation.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if not res:
        err("NOT_FOUND", "Rezervasyon bulunamadı.", 404)

    guest = (await db.execute(select(Guest).where(Guest.id == res.guest_id))).scalar_one_or_none()
    if not guest or (guest.email or "").lower() != email.lower():
        # E-posta eşleşmiyorsa varlığını da doğrulama (enumeration koruması)
        err("NOT_FOUND", "Rezervasyon bulunamadı.", 404)

    rt = (await db.execute(select(RoomType).where(RoomType.id == res.room_type_id))).scalar_one_or_none()
    return PublicBookingResponse(
        reservation_number=res.reservation_number,
        status=str(getattr(res.status, "value", res.status) or "confirmed"),
        room_type_name=rt.name if rt else "-",
        check_in=res.check_in,
        check_out=res.check_out,
        nights=_nights(res.check_in, res.check_out),
        total_amount=res.total_amount or Decimal("0"),
        guest_name=f"{guest.first_name} {guest.last_name}",
        channels_notified=0,
    )
