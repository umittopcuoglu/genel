"""
Front Office service katmani: is mantigi, check-in/out, oda atama.
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.front_office import (
    Room, RoomType, Guest, Reservation, Stay, Trace,
    RoomStatus, ReservationStatus, ReservationSource,
    TracePriority, TraceStatus,
)
from app.schemas.front_office import (
    ReservationCreate, CheckInRequest, CheckOutRequest,
    TraceCreate,
)


class FrontOfficeService:
    """On Büro is mantigi servisi."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ──── RoomType ────

    async def create_room_type(self, data: dict) -> RoomType:
        rt = RoomType(**data)
        self.db.add(rt)
        await self.db.commit()
        await self.db.refresh(rt)
        return rt

    async def get_room_types(self, active_only: bool = True) -> list[RoomType]:
        stmt = select(RoomType)
        if active_only:
            stmt = stmt.where(RoomType.is_active.is_(True), RoomType.deleted_at.is_(None))
        stmt = stmt.order_by(RoomType.code)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_room_type(self, room_type_id: uuid.UUID) -> Optional[RoomType]:
        stmt = select(RoomType).where(RoomType.id == room_type_id, RoomType.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_room_type(self, room_type_id: uuid.UUID, data: dict) -> Optional[RoomType]:
        rt = await self.get_room_type(room_type_id)
        if not rt:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(rt, key, value)
        await self.db.commit()
        await self.db.refresh(rt)
        return rt

    async def delete_room_type(self, room_type_id: uuid.UUID) -> bool:
        rt = await self.get_room_type(room_type_id)
        if not rt:
            return False
        rt.soft_delete()
        await self.db.commit()
        return True

    # ──── Room ────

    async def create_room(self, data: dict) -> Room:
        room = Room(**data)
        self.db.add(room)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def get_rooms(
        self,
        status_filter: Optional[str] = None,
        floor: Optional[int] = None,
        room_type_id: Optional[uuid.UUID] = None,
        active_only: bool = True,
    ) -> list[Room]:
        stmt = select(Room).options(selectinload(Room.room_type))
        conditions = [Room.deleted_at.is_(None)]
        if active_only:
            conditions.append(Room.is_active.is_(True))
        if status_filter:
            conditions.append(Room.status == status_filter)
        if floor is not None:
            conditions.append(Room.floor == floor)
        if room_type_id:
            conditions.append(Room.room_type_id == room_type_id)
        stmt = stmt.where(and_(*conditions)).order_by(Room.room_number)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_room(self, room_id: uuid.UUID) -> Optional[Room]:
        stmt = select(Room).options(selectinload(Room.room_type)).where(
            Room.id == room_id, Room.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_room_by_number(self, room_number: str) -> Optional[Room]:
        stmt = select(Room).options(selectinload(Room.room_type)).where(
            Room.room_number == room_number, Room.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_room(self, room_id: uuid.UUID, data: dict) -> Optional[Room]:
        room = await self.get_room(room_id)
        if not room:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(room, key, value)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def update_room_status(self, room_id: uuid.UUID, status: str) -> Optional[Room]:
        room = await self.get_room(room_id)
        if not room:
            return None
        room.status = RoomStatus(status)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def get_available_rooms(
        self,
        check_in: date,
        check_out: date,
        room_type_id: Optional[uuid.UUID] = None,
    ) -> list[Room]:
        """Belirtilen tarih araliginda bos odalari getir."""
        stmt = select(Room).options(selectinload(Room.room_type)).where(
            Room.deleted_at.is_(None),
            Room.is_active.is_(True),
            Room.status.in_([RoomStatus.CLEAN, RoomStatus.INSPECTED]),
        )
        if room_type_id:
            stmt = stmt.where(Room.room_type_id == room_type_id)
        result = await self.db.execute(stmt)
        all_rooms = list(result.scalars().all())

        # Rezervasyon kontrolu ile cakisanlari filtrele
        busy_room_ids = await self._get_busy_room_ids(check_in, check_out)
        return [r for r in all_rooms if r.id not in busy_room_ids]

    async def _get_busy_room_ids(self, check_in: date, check_out: date) -> set[uuid.UUID]:
        """Belirtilen tarih araliginda dolu odalarin ID'lerini dondur."""
        stmt = select(Stay.room_id).where(
            Stay.is_checked_in.is_(True),
            Stay.is_checked_out.is_(False),
            Stay.deleted_at.is_(None),
            Stay.actual_check_in.isnot(None),
        )
        result = await self.db.execute(stmt)
        occupied = set(row[0] for row in result.all())

        # Rezerve edilmis ama henuz check-in yapilmamis odalar
        stmt2 = select(Reservation.assigned_room_id).where(
            Reservation.status.in_([ReservationStatus.CONFIRMED]),
            Reservation.deleted_at.is_(None),
            Reservation.assigned_room_id.isnot(None),
            Reservation.check_in < check_out,
            Reservation.check_out > check_in,
        )
        result2 = await self.db.execute(stmt2)
        reserved = set(row[0] for row in result2.all())

        return occupied | reserved

    # ──── Guest ────

    async def create_guest(self, data: dict) -> Guest:
        guest = Guest(**data)
        self.db.add(guest)
        await self.db.commit()
        await self.db.refresh(guest)
        return guest

    async def get_guest(self, guest_id: uuid.UUID) -> Optional[Guest]:
        stmt = select(Guest).where(Guest.id == guest_id, Guest.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def search_guests(self, query: str, page: int = 1, limit: int = 20) -> tuple[list[Guest], int]:
        """Isim, email veya telefona gore misafir ara."""
        q = f"%{query}%"
        stmt = select(Guest).where(
            Guest.deleted_at.is_(None),
            or_(
                Guest.first_name.ilike(q),
                Guest.last_name.ilike(q),
                Guest.email.ilike(q),
                Guest.phone.ilike(q),
            )
        ).order_by(Guest.last_name, Guest.first_name)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def update_guest(self, guest_id: uuid.UUID, data: dict) -> Optional[Guest]:
        guest = await self.get_guest(guest_id)
        if not guest:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(guest, key, value)
        await self.db.commit()
        await self.db.refresh(guest)
        return guest

    # ──── Reservation ────

    async def _generate_reservation_number(self) -> str:
        """Yeni rezervasyon numarasi uret: RES-{YYMMDD}-{XXXX}."""
        today = date.today()
        prefix = f"RES-{today.strftime('%y%m%d')}-"
        stmt = select(func.count()).select_from(Reservation).where(
            Reservation.reservation_number.like(f"{prefix}%")
        )
        result = await self.db.execute(stmt)
        count = result.scalar_one()
        return f"{prefix}{count + 1:04d}"

    async def create_reservation(self, data: ReservationCreate) -> Reservation:
        reservation = Reservation(
            reservation_number=await self._generate_reservation_number(),
            guest_id=data.guest_id,
            check_in=data.check_in,
            check_out=data.check_out,
            source=ReservationSource(data.source),
            adults=data.adults,
            children=data.children,
            room_type_id=data.room_type_id,
            assigned_room_id=data.assigned_room_id,
            requested_room_number=data.requested_room_number,
            special_requests=data.special_requests,
            payment_method=data.payment_method,
            deposit_amount=data.deposit_amount,
            deposit_paid=data.deposit_paid,
            channel_ref=data.channel_ref,
        )
        self.db.add(reservation)
        await self.db.commit()
        await self.db.refresh(reservation)
        # Oda atandiysa statusunu reserved yap
        if data.assigned_room_id:
            await self.update_room_status(data.assigned_room_id, "reserved")
        return reservation

    async def get_reservation(self, reservation_id: uuid.UUID) -> Optional[Reservation]:
        stmt = select(Reservation).options(
            selectinload(Reservation.guest),
            selectinload(Reservation.room_type),
            selectinload(Reservation.assigned_room).selectinload(Room.room_type),
            selectinload(Reservation.stays),
        ).where(Reservation.id == reservation_id, Reservation.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_reservations(
        self,
        status_filter: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Reservation], int]:
        stmt = select(Reservation).options(
            selectinload(Reservation.guest),
        ).where(Reservation.deleted_at.is_(None))
        if status_filter:
            stmt = stmt.where(Reservation.status == status_filter)
        if date_from:
            stmt = stmt.where(Reservation.check_in >= date_from)
        if date_to:
            stmt = stmt.where(Reservation.check_out <= date_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(Reservation.check_in).offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def update_reservation(self, reservation_id: uuid.UUID, data: dict) -> Optional[Reservation]:
        res = await self.get_reservation(reservation_id)
        if not res:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(res, key, value)
        await self.db.commit()
        await self.db.refresh(res)
        return res

    async def cancel_reservation(self, reservation_id: uuid.UUID, reason: str) -> Optional[Reservation]:
        res = await self.get_reservation(reservation_id)
        if not res:
            return None
        res.status = ReservationStatus.CANCELLED
        res.cancellation_reason = reason
        res.cancelled_at = datetime.now(timezone.utc)
        if res.assigned_room_id:
            await self.update_room_status(res.assigned_room_id, "clean")
        await self.db.commit()
        await self.db.refresh(res)
        return res

    async def get_arrivals(self, target_date: date) -> list[Reservation]:
        """Belirtilen tarihte gelmesi beklenen rezervasyonlar."""
        stmt = select(Reservation).options(
            selectinload(Reservation.guest),
            selectinload(Reservation.room_type),
        ).where(
            Reservation.deleted_at.is_(None),
            Reservation.check_in == target_date,
            Reservation.status.in_([ReservationStatus.CONFIRMED]),
        ).order_by(Reservation.guest_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_departures(self, target_date: date) -> list[Reservation]:
        """Belirtilen tarihte cikis yapmasi beklenen rezervasyonlar."""
        stmt = select(Reservation).options(
            selectinload(Reservation.guest),
            selectinload(Reservation.stays),
        ).where(
            Reservation.deleted_at.is_(None),
            Reservation.check_out == target_date,
            Reservation.status == ReservationStatus.CHECKED_IN,
        ).order_by(Reservation.guest_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_in_house(self) -> list[Stay]:
        """Su anda oteldeki konaklamalar."""
        stmt = select(Stay).options(
            selectinload(Stay.guest),
            selectinload(Stay.room).selectinload(Room.room_type),
            selectinload(Stay.reservation),
        ).where(
            Stay.is_checked_in.is_(True),
            Stay.is_checked_out.is_(False),
            Stay.deleted_at.is_(None),
        ).order_by(Stay.actual_check_in)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ──── Check-in / Check-out ────

    async def check_in(self, data: CheckInRequest) -> Optional[Stay]:
        """Check-in islemi: Stay olustur, oda ve rezervasyon durumunu guncelle."""
        reservation = await self.get_reservation(data.reservation_id)
        if not reservation:
            return None
        if reservation.status not in [ReservationStatus.CONFIRMED, ReservationStatus.RESERVED]:
            return None

        # Odayi kontrol et
        room = await self.get_room(data.room_id)
        if not room or room.status not in [RoomStatus.CLEAN, RoomStatus.INSPECTED, RoomStatus.RESERVED]:
            return None

        # Stay olustur
        stay = Stay(
            reservation_id=reservation.id,
            room_id=room.id,
            guest_id=reservation.guest_id,
            actual_check_in=datetime.now(timezone.utc),
            pax_count=data.pax_count,
            folio_balance=reservation.deposit_amount,
            is_checked_in=True,
            is_checked_out=False,
            notes=data.notes,
        )
        self.db.add(stay)

        # Rezervasyon ve oda durumunu guncelle
        reservation.status = ReservationStatus.CHECKED_IN
        reservation.assigned_room_id = room.id
        reservation.checked_in_at = datetime.now(timezone.utc)
        room.status = RoomStatus.OCCUPIED

        await self.db.commit()
        await self.db.refresh(stay)
        return stay

    async def check_out(self, data: CheckOutRequest) -> Optional[Stay]:
        """Check-out islemi: Stay kapat, oda durumunu dirty yap."""
        stay = await self.db.get(Stay, data.stay_id)
        if not stay or stay.deleted_at or not stay.is_checked_in or stay.is_checked_out:
            return None

        stay.is_checked_out = True
        stay.actual_check_out = datetime.now(timezone.utc)
        if data.notes:
            stay.notes = (stay.notes or "") + f" | Check-out: {data.notes}"

        # Rezervasyonu guncelle
        reservation = await self.get_reservation(stay.reservation_id)
        if reservation:
            reservation.status = ReservationStatus.CHECKED_OUT
            reservation.checked_out_at = datetime.now(timezone.utc)

        # Odayi dirty yap
        room = await self.get_room(stay.room_id)
        if room:
            room.status = RoomStatus.DIRTY

        await self.db.commit()
        await self.db.refresh(stay)
        return stay

    async def mark_no_show(self, reservation_id: uuid.UUID) -> Optional[Reservation]:
        """Rezervasyonu no-show olarak isaretle."""
        res = await self.get_reservation(reservation_id)
        if not res:
            return None
        if res.status != ReservationStatus.CONFIRMED:
            return None
        res.status = ReservationStatus.NO_SHOW
        res.no_show_marked_at = datetime.now(timezone.utc)
        if res.assigned_room_id:
            await self.update_room_status(res.assigned_room_id, "clean")
        await self.db.commit()
        await self.db.refresh(res)
        return res

    # ──── Trace ────

    async def create_trace(self, data: TraceCreate) -> Trace:
        trace = Trace(
            reservation_id=data.reservation_id,
            stay_id=data.stay_id,
            guest_id=data.guest_id,
            room_id=data.room_id,
            department=data.department,
            subject=data.subject,
            description=data.description,
            priority=TracePriority(data.priority),
            assigned_to=data.assigned_to,
            due_date=data.due_date,
        )
        self.db.add(trace)
        await self.db.commit()
        await self.db.refresh(trace)
        return trace

    async def get_traces(
        self,
        department: Optional[str] = None,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        reservation_id: Optional[uuid.UUID] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Trace], int]:
        stmt = select(Trace).where(Trace.deleted_at.is_(None))
        if department:
            stmt = stmt.where(Trace.department == department)
        if status_filter:
            stmt = stmt.where(Trace.status == status_filter)
        if priority_filter:
            stmt = stmt.where(Trace.priority == priority_filter)
        if reservation_id:
            stmt = stmt.where(Trace.reservation_id == reservation_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(Trace.created_at.desc()).offset((page - 1) * limit).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def resolve_trace(self, trace_id: uuid.UUID, resolution_notes: str) -> Optional[Trace]:
        trace = await self.db.get(Trace, trace_id)
        if not trace or trace.deleted_at:
            return None
        trace.status = TraceStatus.RESOLVED
        trace.resolved_at = datetime.now(timezone.utc)
        trace.resolution_notes = resolution_notes
        await self.db.commit()
        await self.db.refresh(trace)
        return trace
