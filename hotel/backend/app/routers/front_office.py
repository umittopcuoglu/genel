"""
Front Office API router: oda, misafir, rezervasyon, check-in/out, trace endpoint'leri.
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_roles
from app.models.user import User
from app.schemas.front_office import (
    RoomTypeCreate, RoomTypeUpdate, RoomTypeResponse,
    RoomCreate, RoomUpdate, RoomResponse,
    GuestCreate, GuestUpdate, GuestResponse, GuestSearchParams, GuestSearchResponse,
    ReservationCreate, ReservationUpdate, ReservationResponse,
    CheckInRequest, CheckInResponse, CheckOutRequest, CheckOutResponse,
    TraceCreate, TraceUpdate, TraceResponse,
)
from app.services.front_office import FrontOfficeService
from app.models.front_office import Reservation, Stay

router = APIRouter()


# ──── Helper ────

async def get_fo_service(db: AsyncSession = Depends(get_db)) -> FrontOfficeService:
    return FrontOfficeService(db)


def not_found(entity: str = "Kayit"):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": {
                "code": "NOT_FOUND",
                "message": f"{entity} bulunamadi.",
                "details": {}
            }
        }
    )


# ──── Room Types ────

@router.get("/room-types", response_model=list[RoomTypeResponse], summary="Oda tiplerini listele")
async def list_room_types(
    service: FrontOfficeService = Depends(get_fo_service),
):
    return await service.get_room_types()


@router.get("/room-types/{room_type_id}", response_model=RoomTypeResponse, summary="Oda tipi detayi")
async def get_room_type(
    room_type_id: uuid.UUID,
    service: FrontOfficeService = Depends(get_fo_service),
):
    rt = await service.get_room_type(room_type_id)
    if not rt:
        not_found("Oda tipi")
    return rt


@router.post("/room-types", response_model=RoomTypeResponse, status_code=status.HTTP_201_CREATED, summary="Oda tipi ekle")
async def create_room_type(
    data: RoomTypeCreate,
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    return await service.create_room_type(data.model_dump())


@router.put("/room-types/{room_type_id}", response_model=RoomTypeResponse, summary="Oda tipi guncelle")
async def update_room_type(
    room_type_id: uuid.UUID,
    data: RoomTypeUpdate,
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    rt = await service.update_room_type(room_type_id, data.model_dump(exclude_unset=True))
    if not rt:
        not_found("Oda tipi")
    return rt


@router.delete("/room-types/{room_type_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Oda tipi sil")
async def delete_room_type(
    room_type_id: uuid.UUID,
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    if not await service.delete_room_type(room_type_id):
        not_found("Oda tipi")


# ──── Rooms ────

@router.get("/rooms", response_model=list[RoomResponse], summary="Odalari listele")
async def list_rooms(
    status: Optional[str] = Query(None, description="Oda durumu filtre"),
    floor: Optional[int] = Query(None, description="Kat filtre"),
    room_type_id: Optional[uuid.UUID] = Query(None, description="Oda tipi filtre"),
    service: FrontOfficeService = Depends(get_fo_service),
):
    return await service.get_rooms(status_filter=status, floor=floor, room_type_id=room_type_id)


@router.get("/rooms/available", response_model=list[RoomResponse], summary="Musait odalari listele")
async def list_available_rooms(
    check_in: date = Query(..., description="Giris tarihi"),
    check_out: date = Query(..., description="Cikis tarihi"),
    room_type_id: Optional[uuid.UUID] = Query(None, description="Oda tipi filtre"),
    service: FrontOfficeService = Depends(get_fo_service),
):
    return await service.get_available_rooms(check_in, check_out, room_type_id)


@router.get("/rooms/{room_id}", response_model=RoomResponse, summary="Oda detayi")
async def get_room(
    room_id: uuid.UUID,
    service: FrontOfficeService = Depends(get_fo_service),
):
    room = await service.get_room(room_id)
    if not room:
        not_found("Oda")
    return room


@router.post("/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED, summary="Oda ekle")
async def create_room(
    data: RoomCreate,
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    return await service.create_room(data.model_dump())


@router.put("/rooms/{room_id}", response_model=RoomResponse, summary="Oda guncelle")
async def update_room(
    room_id: uuid.UUID,
    data: RoomUpdate,
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    room = await service.update_room(room_id, data.model_dump(exclude_unset=True))
    if not room:
        not_found("Oda")
    return room


# ──── Guests ────

@router.get("/guests/search", response_model=GuestSearchResponse, summary="Misafir ara")
async def search_guests(
    query: str = Query(..., min_length=2, description="Isim, email veya telefon"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(get_current_user),
):
    items, total = await service.search_guests(query, page, limit)
    return GuestSearchResponse(items=items, total=total, page=page, limit=limit)


@router.get("/guests/{guest_id}", response_model=GuestResponse, summary="Misafir detayi")
async def get_guest(
    guest_id: uuid.UUID,
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(get_current_user),
):
    guest = await service.get_guest(guest_id)
    if not guest:
        not_found("Misafir")
    return guest


@router.post("/guests", response_model=GuestResponse, status_code=status.HTTP_201_CREATED, summary="Misafir ekle")
async def create_guest(
    data: GuestCreate,
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(get_current_user),
):
    return await service.create_guest(data.model_dump())


@router.put("/guests/{guest_id}", response_model=GuestResponse, summary="Misafir guncelle")
async def update_guest(
    guest_id: uuid.UUID,
    data: GuestUpdate,
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(get_current_user),
):
    guest = await service.update_guest(guest_id, data.model_dump(exclude_unset=True))
    if not guest:
        not_found("Misafir")
    return guest


# ──── Reservations ────

@router.get("/reservations", response_model=list[ReservationResponse], summary="Rezervasyon listesi")
async def list_reservations(
    status: Optional[str] = Query(None, description="Durum filtre"),
    date_from: Optional[date] = Query(None, description="Baslangic tarihi"),
    date_to: Optional[date] = Query(None, description="Bitis tarihi"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(get_current_user),
):
    items, total = await service.get_reservations(status, date_from, date_to, page, limit)
    return items


@router.get("/reservations/arrivals", response_model=list[ReservationResponse], summary="Bugun gelecekler")
async def get_arrivals(
    target_date: Optional[date] = Query(default=None, description="Tarih (bos ise bugun)"),
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(get_current_user),
):
    if target_date is None:
        target_date = date.today()
    return await service.get_arrivals(target_date)


@router.get("/reservations/departures", response_model=list[ReservationResponse], summary="Bugun cikis yapacaklar")
async def get_departures(
    target_date: Optional[date] = Query(default=None, description="Tarih (bos ise bugun)"),
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(get_current_user),
):
    if target_date is None:
        target_date = date.today()
    return await service.get_departures(target_date)


@router.get("/reservations/in-house", response_model=list[ReservationResponse], summary="Oteldeki misafirler")
async def get_in_house(
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(get_current_user),
):
    """Su anda otelde konaklayan misafirlerin rezervasyon bilgilerini dondurur."""
    stays = await service.get_in_house()
    reservations = []
    for stay in stays:
        if stay.reservation:
            reservations.append(stay.reservation)
    return reservations


@router.get("/reservations/{reservation_id}", response_model=ReservationResponse, summary="Rezervasyon detayi")
async def get_reservation(
    reservation_id: uuid.UUID,
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(get_current_user),
):
    res = await service.get_reservation(reservation_id)
    if not res:
        not_found("Rezervasyon")
    return res


@router.post("/reservations", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED, summary="Rezervasyon olustur")
async def create_reservation(
    data: ReservationCreate,
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    return await service.create_reservation(data)


@router.put("/reservations/{reservation_id}", response_model=ReservationResponse, summary="Rezervasyon guncelle")
async def update_reservation(
    reservation_id: uuid.UUID,
    data: ReservationUpdate,
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    res = await service.update_reservation(reservation_id, data.model_dump(exclude_unset=True))
    if not res:
        not_found("Rezervasyon")
    return res


@router.post("/reservations/{reservation_id}/cancel", response_model=ReservationResponse, summary="Rezervasyon iptal")
async def cancel_reservation(
    reservation_id: uuid.UUID,
    reason: str = Query(..., min_length=3, description="Iptal sebebi"),
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    res = await service.cancel_reservation(reservation_id, reason)
    if not res:
        not_found("Rezervasyon")
    return res


# ──── Check-in / Check-out ────

@router.post("/check-in", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED, summary="Check-in")
async def check_in(
    data: CheckInRequest,
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    stay = await service.check_in(data)
    if not stay:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "CHECK_IN_FAILED",
                    "message": "Check-in basarisiz. Rezervasyon veya oda uygun degil.",
                    "details": {}
                }
            }
        )
    res = await service.get_reservation(data.reservation_id)
    room = await service.get_room(data.room_id)

    # TASK-006: WebSocket emit
    from app.ws.events import emit_checkin
    guest_name = f"{res.guest.first_name} {res.guest.last_name}" if res.guest else ""
    await emit_checkin(str(res.id), room.room_number, guest_name)

    # B1: Domain event yayını — HK/CRM/IoT abonelikleri için
    from app.core.events import CheckInCompleted, events as _events
    await _events.publish(
        CheckInCompleted(
            reservation_id=res.id,
            guest_id=res.guest_id,
            room_id=room.id,
        ),
        db=service.db if hasattr(service, "db") else None,
    )

    return CheckInResponse(
        stay_id=stay.id,
        reservation=res,
        room=room,
        message="Check-in basariyla tamamlandi."
    )


@router.post("/check-out", response_model=CheckOutResponse, summary="Check-out")
async def check_out(
    data: CheckOutRequest,
    db: AsyncSession = Depends(get_db),
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    stay = await service.check_out(data)
    if not stay:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "CHECK_OUT_FAILED",
                    "message": "Check-out basarisiz. Konaklama kaydi bulunamadi veya zaten cikis yapilmis.",
                    "details": {}
                }
            }
        )

    # TASK-004: Gercek folio'dan balance oku
    from app.models.finance import Folio
    folio_stmt = select(Folio).where(
        Folio.reservation_id == stay.reservation_id,
        Folio.deleted_at.is_(None),
    )
    folio_result = await db.execute(folio_stmt)
    folio = folio_result.scalar_one_or_none()
    folio_balance = folio.balance if folio else Decimal("0")

    if folio_balance > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "OUTSTANDING_BALANCE",
                    "message": f"Check-out yapilamaz. Kalan bakiye: {folio_balance}",
                    "details": {"balance": str(folio_balance)}
                }
            }
        )

    # TASK-006: WebSocket emit
    from app.ws.events import emit_checkout
    guest_name = ""
    try:
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select as sel2
        from app.models.front_office import Reservation as ResModel
        r_stmt = sel2(ResModel).options(selectinload(ResModel.guest)).where(ResModel.id == stay.reservation_id)
        r_res = await db.execute(r_stmt)
        r = r_res.scalar_one_or_none()
        if r and r.guest:
            guest_name = f"{r.guest.first_name} {r.guest.last_name}"
    except Exception:
        pass
    room_no = ""
    try:
        from app.models.front_office import Room as RoomModel
        r_stmt2 = sel2(RoomModel).where(RoomModel.id == stay.room_id)
        r_res2 = await db.execute(r_stmt2)
        rm = r_res2.scalar_one_or_none()
        if rm:
            room_no = rm.room_number
    except Exception:
        pass
    await emit_checkout(str(stay.reservation_id), room_no, guest_name)

    # B1: Domain event — Revenue recompute, CRM teşekkür mesajı
    from app.core.events import CheckOutCompleted, events as _events
    await _events.publish(
        CheckOutCompleted(
            reservation_id=stay.reservation_id,
            folio_total=float(folio_balance) if folio_balance else 0.0,
        ),
        db=db,
    )

    return CheckOutResponse(
        stay_id=stay.id,
        folio_balance=folio_balance,
        message="Check-out basariyla tamamlandi."
    )
@router.post("/reservations/{reservation_id}/no-show", response_model=ReservationResponse, summary="No-show isaretle")
async def mark_no_show(
    reservation_id: uuid.UUID,
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    res = await service.mark_no_show(reservation_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "NO_SHOW_FAILED",
                    "message": "No-show isaretlenemedi. Rezervasyon durumu uygun degil.",
                    "details": {}
                }
            }
        )
    return res


# ──── Traces ────

@router.get("/traces", response_model=list[TraceResponse], summary="Trace listesi")
async def list_traces(
    department: Optional[str] = Query(None, description="Departman filtre"),
    status: Optional[str] = Query(None, description="Durum filtre"),
    priority: Optional[str] = Query(None, description="Oncelik filtre"),
    reservation_id: Optional[uuid.UUID] = Query(None, description="Rezervasyon ID filtre"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(get_current_user),
):
    items, total = await service.get_traces(department, status, priority, reservation_id, page, limit)
    return items


@router.post("/traces", response_model=TraceResponse, status_code=status.HTTP_201_CREATED, summary="Trace ekle")
async def create_trace(
    data: TraceCreate,
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(get_current_user),
):
    return await service.create_trace(data)


@router.post("/traces/{trace_id}/resolve", response_model=TraceResponse, summary="Trace coz")
async def resolve_trace(
    trace_id: uuid.UUID,
    resolution_notes: str = Query(..., min_length=3, description="Cozum notlari"),
    service: FrontOfficeService = Depends(get_fo_service),
    current_user: User = Depends(get_current_user),
):
    trace = await service.resolve_trace(trace_id, resolution_notes)
    if not trace:
        not_found("Trace")
    return trace
