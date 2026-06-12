"""Revenue Management / RevenueIQ servisi.

- Dinamik fiyatlama önerileri (talep + doluluk + tarihsel ortalama bazlı)
- Doluluk tahmini (basit zaman-serisi ortalaması)
- Overbooking kuralları
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.front_office import Reservation, Room, RoomType
from app.models.occupancy_forecast import OccupancyForecast
from app.models.overbooking_rule import OverbookingRule
from app.models.rate_recommendation import RateRecommendation
from app.models.reservation_ext import RatePlan


class RevenueService:
    # ── Doluluk tahmini ──

    @staticmethod
    async def forecast_occupancy(
        db: AsyncSession,
        target_date: date,
        room_type_id: Optional[UUID] = None,
        horizon_days: int = 30,
    ) -> OccupancyForecast:
        """Hedef tarih için doluluk yüzdesi tahmini.

        Yöntem (mock-AI, gerçekçi heuristic):
          - Aynı hafta günü için son 4 haftanın ortalama doluluğu (mevcut rezervasyonlar)
          - Mevsimsel etken (yaz +%15, kış -%10)
          - 0-100 arası clip
        """
        # Toplam oda sayısı
        room_q = select(func.count(Room.id)).where(Room.is_active.is_(True), Room.deleted_at.is_(None))
        if room_type_id:
            room_q = room_q.where(Room.room_type_id == room_type_id)
        total_rooms = (await db.execute(room_q)).scalar() or 0

        # Aynı hafta günü için son 4 hafta
        weekly_occupancies: list[float] = []
        for w in range(1, 5):
            ref = target_date - timedelta(weeks=w)
            res_q = select(func.count(Reservation.id)).where(
                and_(
                    Reservation.check_in <= ref,
                    Reservation.check_out > ref,
                    Reservation.deleted_at.is_(None),
                    Reservation.status.in_(("confirmed", "checked_in", "checked_out")),
                )
            )
            if room_type_id:
                res_q = res_q.where(Reservation.room_type_id == room_type_id)
            occupied = (await db.execute(res_q)).scalar() or 0
            if total_rooms > 0:
                weekly_occupancies.append(100 * occupied / total_rooms)

        base = sum(weekly_occupancies) / len(weekly_occupancies) if weekly_occupancies else 50.0

        # Mevsimsel etken
        seasonal = 0.0
        if target_date.month in (6, 7, 8):
            seasonal = 15.0
        elif target_date.month in (12, 1, 2):
            seasonal = -10.0
        predicted = max(0.0, min(100.0, base + seasonal))

        forecast = OccupancyForecast(
            room_type_id=room_type_id,
            forecast_date=target_date.isoformat(),
            predicted_occupancy_percent=round(predicted, 2),
            predicted_rooms_occupied=int(round(total_rooms * predicted / 100)),
            confidence_interval=f"{max(0, predicted-10):.0f}%-{min(100, predicted+10):.0f}%",
            forecast_method="4-week-moving-avg + seasonal",
            forecast_horizon_days=horizon_days,
        )
        db.add(forecast)
        await db.commit()
        await db.refresh(forecast)
        return forecast

    # ── Fiyat önerisi ──

    @staticmethod
    async def recommend_rate(
        db: AsyncSession,
        room_type_id: UUID,
        target_date: date,
        competitor_avg_rate: Optional[Decimal] = None,
    ) -> RateRecommendation:
        """Tarih + oda tipi için fiyat önerisi.

        Karar matrisi (basit):
          - Tahmini doluluk > %85 → fiyatı %15 artır (talep yüksek)
          - %60-85 → %5 artır
          - %30-60 → mevcut fiyatı koru
          - < %30 → %10 düşür (talep düşük, doluluk hedefli)
        """
        rt = await db.get(RoomType, room_type_id)
        if rt is None:
            raise ValueError("Oda tipi bulunamadı")

        # Mevcut rate (active rate plan'dan veya default'tan)
        rp_res = await db.execute(
            select(RatePlan).where(
                RatePlan.room_type_id == room_type_id,
                RatePlan.is_active.is_(True),
                RatePlan.deleted_at.is_(None),
            ).limit(1)
        )
        rp = rp_res.scalars().first()
        current_rate = Decimal(rp.base_rate if rp else rt.default_rate)

        forecast = await RevenueService.forecast_occupancy(db, target_date, room_type_id)
        occ = forecast.predicted_occupancy_percent

        if occ > 85:
            mult, trend = Decimal("1.15"), "yüksek talep"
        elif occ > 60:
            mult, trend = Decimal("1.05"), "orta talep"
        elif occ > 30:
            mult, trend = Decimal("1.00"), "stabil"
        else:
            mult, trend = Decimal("0.90"), "düşük talep"

        recommended = (current_rate * mult).quantize(Decimal("0.01"))
        # Rakip fiyatı varsa -%5 / +%10 bandında sıkıştır
        if competitor_avg_rate:
            lower = competitor_avg_rate * Decimal("0.95")
            upper = competitor_avg_rate * Decimal("1.10")
            recommended = max(lower, min(upper, recommended)).quantize(Decimal("0.01"))

        change_pct = float((recommended - current_rate) / current_rate * 100) if current_rate > 0 else 0.0

        rec = RateRecommendation(
            room_type_id=room_type_id,
            date=target_date.isoformat(),
            recommended_rate=recommended,
            current_rate=current_rate,
            price_change_percent=round(change_pct, 2),
            rationale=(
                f"Tahmini doluluk %{occ:.0f} ({trend}). "
                f"Önerilen değişim: %{change_pct:+.1f}."
            ),
            confidence_score=0.78 if occ > 30 else 0.55,
            historical_avg_rate=current_rate,
            occupancy_forecast=occ,
            demand_trend=trend,
            competitor_avg_rate=competitor_avg_rate,
            status="suggested",
        )
        db.add(rec)
        await db.commit()
        await db.refresh(rec)
        return rec

    @staticmethod
    async def approve_recommendation(db: AsyncSession, rec_id: UUID) -> RateRecommendation:
        rec = await db.get(RateRecommendation, rec_id)
        if rec is None:
            raise ValueError("Öneri bulunamadı")
        rec.status = "approved"
        # Aktif rate plan'ı güncelle
        rp_res = await db.execute(
            select(RatePlan).where(
                RatePlan.room_type_id == rec.room_type_id,
                RatePlan.is_active.is_(True),
                RatePlan.deleted_at.is_(None),
            ).limit(1)
        )
        rp = rp_res.scalars().first()
        if rp:
            rp.base_rate = rec.recommended_rate
        await db.commit()
        await db.refresh(rec)
        return rec

    @staticmethod
    async def reject_recommendation(db: AsyncSession, rec_id: UUID) -> RateRecommendation:
        rec = await db.get(RateRecommendation, rec_id)
        if rec is None:
            raise ValueError("Öneri bulunamadı")
        rec.status = "rejected"
        await db.commit()
        await db.refresh(rec)
        return rec

    # ── Overbooking ──

    @staticmethod
    async def upsert_overbooking_rule(
        db: AsyncSession,
        room_type_id: Optional[UUID],
        channel_id: Optional[UUID],
        overbooking_percent: float,
        note: Optional[str] = None,
        enabled: bool = True,
    ) -> OverbookingRule:
        if overbooking_percent < 0 or overbooking_percent > 50:
            raise ValueError("Overbooking yüzdesi 0-50 aralığında olmalı")
        # Aynı (room_type, channel) için varsa güncelle
        existing = await db.execute(
            select(OverbookingRule).where(
                OverbookingRule.room_type_id == room_type_id,
                OverbookingRule.channel_id == channel_id,
                OverbookingRule.deleted_at.is_(None),
            )
        )
        rule = existing.scalars().first()
        if rule:
            rule.overbooking_percent = overbooking_percent
            rule.enabled = enabled
            rule.note = note
        else:
            rule = OverbookingRule(
                room_type_id=room_type_id,
                channel_id=channel_id,
                overbooking_percent=overbooking_percent,
                enabled=enabled,
                note=note,
            )
            db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule
