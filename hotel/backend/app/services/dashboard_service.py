from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.room import Room
from app.models.reservation import Reservation
from app.models.folio import Folio


class DashboardService:
    @staticmethod
    async def calculate_kpis(from_date: date, to_date: date, db: AsyncSession) -> dict:
        """KPI'ları hesapla."""

        total_rooms = await db.execute(select(func.count(Room.id)))
        total_room_count = total_rooms.scalar() or 1
        days = (to_date - from_date).days + 1

        occupied = await db.execute(
            select(func.count(Reservation.id))
            .where(
                Reservation.checkin_date <= to_date,
                Reservation.checkout_date > from_date,
                Reservation.status.notin_(["cancelled", "no_show"]),
            )
        )
        occupied_count = occupied.scalar() or 0

        occupancy_percent = (
            (occupied_count / (total_room_count * days)) * 100 if total_room_count > 0 else 0
        )

        adr = await db.execute(
            select(func.avg(Folio.total_amount))
            .where(
                Folio.closed_date >= from_date,
                Folio.closed_date <= to_date,
            )
        )
        adr_value = float(adr.scalar() or 0)

        total_revenue = await db.execute(
            select(func.sum(Folio.total_amount))
            .where(
                Folio.closed_date >= from_date,
                Folio.closed_date <= to_date,
            )
        )
        total_rev = float(total_revenue.scalar() or 0)

        revpar = (
            (total_rev / (total_room_count * days))
            if total_room_count > 0
            else 0
        )

        arrivals = await db.execute(
            select(func.count(Reservation.id))
            .where(
                Reservation.checkin_date >= from_date,
                Reservation.checkin_date <= to_date,
                Reservation.status.notin_(["cancelled", "no_show"]),
            )
        )
        arrivals_count = arrivals.scalar() or 0

        departures = await db.execute(
            select(func.count(Reservation.id))
            .where(
                Reservation.checkout_date >= from_date,
                Reservation.checkout_date <= to_date,
                Reservation.status.notin_(["cancelled", "no_show"]),
            )
        )
        departures_count = departures.scalar() or 0

        return {
            "occupancy": {
                "percent": round(occupancy_percent, 1),
                "rooms_occupied": occupied_count,
                "total_rooms": total_room_count,
            },
            "adr": {
                "value": round(adr_value, 2),
                "currency": "TL",
            },
            "revpar": {
                "value": round(revpar, 2),
                "currency": "TL",
            },
            "arrivals": arrivals_count,
            "departures": departures_count,
            "ooo_rooms": 0,
        }
