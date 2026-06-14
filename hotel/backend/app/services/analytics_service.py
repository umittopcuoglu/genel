"""
Analitik servis — Gelişmiş Analitik Dashboard (TASK-013 / InsightAI) için
toplulaştırma sorguları: haftalık doluluk trendi (yıl-yıl), aylık gelir trendi,
rezervasyon kaynak dağılımı. Mevcut veriden gerçek-zamanlı hesaplanır.
"""
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.front_office import Stay, Room, Reservation
from app.models.finance import Folio, FolioItem, FolioItemType

# Türkçe etiketler
WEEKDAYS_TR = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
MONTHS_TR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
             "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]

# Rezervasyon kaynağı → ekran etiketi + ton
SOURCE_META = {
    "direct": ("Direct", "primary"),
    "ota": ("OTA", "info"),
    "corporate": ("Corporate", "success"),
    "walk_in": ("Walk-in", "warning"),
    "channel": ("Channel", "neutral"),
}


async def _total_rooms(db: AsyncSession) -> int:
    stmt = select(func.count()).select_from(Room).where(
        Room.deleted_at.is_(None), Room.is_active.is_(True),
    )
    return (await db.execute(stmt)).scalar_one()


async def _occupied_on(db: AsyncSession, day: date) -> int:
    day_end = datetime.combine(day, datetime.max.time()).replace(tzinfo=timezone.utc)
    stmt = select(func.count()).select_from(Stay).where(
        Stay.is_checked_in.is_(True),
        Stay.deleted_at.is_(None),
        Stay.actual_check_in <= day_end,
        (Stay.actual_check_out.is_(None) | (Stay.actual_check_out > day_end)),
    )
    return (await db.execute(stmt)).scalar_one()


async def occupancy_trend(db: AsyncSession, today: date | None = None) -> list[dict]:
    """Son 7 günün doluluk %'si + geçen yılın aynı günü (secondary)."""
    today = today or date.today()
    total = await _total_rooms(db)
    start = today - timedelta(days=6)
    rows: list[dict] = []
    for i in range(7):
        d = start + timedelta(days=i)
        occ = await _occupied_on(db, d)
        last_year = await _occupied_on(db, d - timedelta(days=364))  # aynı haftagünü
        rows.append({
            "label": WEEKDAYS_TR[d.weekday()],
            "value": round(occ / total * 100, 1) if total > 0 else 0.0,
            "secondary": round(last_year / total * 100, 1) if total > 0 else 0.0,
        })
    return rows


async def _room_revenue_between(db: AsyncSession, start: datetime, end: datetime) -> Decimal:
    stmt = select(func.coalesce(func.sum(FolioItem.total), 0)).select_from(FolioItem).join(
        Folio, FolioItem.folio_id == Folio.id
    ).where(
        FolioItem.type == FolioItemType.ROOM.value,
        FolioItem.deleted_at.is_(None),
        FolioItem.posted_at >= start,
        FolioItem.posted_at <= end,
    )
    return (await db.execute(stmt)).scalar_one() or Decimal("0")


async def revenue_trend(db: AsyncSession, today: date | None = None) -> list[dict]:
    """Son 6 ayın oda geliri (aylık)."""
    today = today or date.today()
    rows: list[dict] = []
    # 5 ay öncesinden bu aya kadar
    year, month = today.year, today.month
    months: list[tuple[int, int]] = []
    for _ in range(6):
        months.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    for (yy, mm) in reversed(months):
        start = datetime(yy, mm, 1, tzinfo=timezone.utc)
        if mm == 12:
            end = datetime(yy + 1, 1, 1, tzinfo=timezone.utc) - timedelta(microseconds=1)
        else:
            end = datetime(yy, mm + 1, 1, tzinfo=timezone.utc) - timedelta(microseconds=1)
        rev = await _room_revenue_between(db, start, end)
        rows.append({"label": MONTHS_TR[mm - 1], "value": float(rev)})
    return rows


async def source_mix(db: AsyncSession) -> list[dict]:
    """Rezervasyon kaynak dağılımı (yüzde)."""
    stmt = select(Reservation.source, func.count()).select_from(Reservation).where(
        Reservation.deleted_at.is_(None)
    ).group_by(Reservation.source)
    result = await db.execute(stmt)
    counts: dict[str, int] = {}
    for src, cnt in result.all():
        key = src.value if hasattr(src, "value") else str(src)
        counts[key] = counts.get(key, 0) + cnt
    total = sum(counts.values())
    rows: list[dict] = []
    for key, cnt in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
        label, tone = SOURCE_META.get(key, (key.capitalize(), "neutral"))
        rows.append({
            "label": label,
            "value": round(cnt / total * 100, 1) if total > 0 else 0.0,
            "tone": tone,
        })
    return rows
