"""InsightAI: doluluk, ADR, RevPAR, kanal dağılımı, gelir KPI'larını tek elden döken servis.

Mevcut `dashboard_service`, `consolidation_service` ve raporları bu katmanda
birleştirir; sezgisel ve aksiyon-önerili özet üretir (LLM yerine kural-tabanlı).
"""
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.channel import Channel
from app.models.finance import Folio
from app.models.front_office import Reservation, Room


class InsightsService:
    @staticmethod
    async def revenue_summary(
        db: AsyncSession, date_from: date, date_to: date
    ) -> dict:
        """Tarih aralığında temel gelir KPI'ları."""
        # Toplam gelir (kapanmış folio'lar)
        rev_q = await db.execute(
            select(func.coalesce(func.sum(Folio.total), 0))
            .where(
                Folio.closed_date >= date_from,
                Folio.closed_date <= date_to,
                Folio.deleted_at.is_(None),
            )
        )
        total_revenue = Decimal(rev_q.scalar() or 0)

        # Konaklama sayısı
        nights_q = await db.execute(
            select(func.count(Reservation.id))
            .where(
                Reservation.check_in >= date_from,
                Reservation.check_in <= date_to,
                Reservation.deleted_at.is_(None),
            )
        )
        total_stays = int(nights_q.scalar() or 0)

        # Toplam oda
        rooms_q = await db.execute(
            select(func.count(Room.id)).where(
                Room.is_active.is_(True), Room.deleted_at.is_(None)
            )
        )
        total_rooms = int(rooms_q.scalar() or 0)

        days = max(1, (date_to - date_from).days + 1)
        adr = float(total_revenue) / total_stays if total_stays else 0.0
        revpar = float(total_revenue) / (total_rooms * days) if total_rooms else 0.0
        occupancy = (total_stays / (total_rooms * days)) * 100 if total_rooms else 0.0

        return {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "total_revenue": float(total_revenue),
            "total_stays": total_stays,
            "adr": round(adr, 2),
            "revpar": round(revpar, 2),
            "occupancy_percent": round(occupancy, 2),
        }

    @staticmethod
    async def channel_mix(db: AsyncSession, date_from: date, date_to: date) -> list[dict]:
        """Kanal başına rezervasyon dağılımı."""
        res = await db.execute(
            select(Reservation.source, func.count(Reservation.id))
            .where(
                Reservation.check_in >= date_from,
                Reservation.check_in <= date_to,
                Reservation.deleted_at.is_(None),
            )
            .group_by(Reservation.source)
        )
        rows = res.all()
        total = sum(r[1] for r in rows) or 1
        return [
            {"channel": (r[0] or "direct"), "count": int(r[1]), "share_percent": round(100 * r[1] / total, 2)}
            for r in rows
        ]

    @staticmethod
    async def actionable_insights(
        db: AsyncSession, date_from: date, date_to: date
    ) -> list[dict]:
        """Kural-tabanlı InsightAI: KPI'lara göre öneri üret."""
        summary = await InsightsService.revenue_summary(db, date_from, date_to)
        mix = await InsightsService.channel_mix(db, date_from, date_to)
        insights: list[dict] = []

        if summary["occupancy_percent"] < 40:
            insights.append({
                "severity": "warning",
                "title": "Düşük doluluk",
                "message": f"Doluluk %{summary['occupancy_percent']:.1f}. Promosyon kampanyası önerilir.",
                "action": "create_campaign",
            })
        if summary["occupancy_percent"] > 85:
            insights.append({
                "severity": "opportunity",
                "title": "Yüksek talep",
                "message": "Doluluk %85 üzerinde — fiyat artırma fırsatı.",
                "action": "review_rate_recommendations",
            })

        # Kanal yoğunlaşması (>%60 tek kanal)
        for row in mix:
            if row["share_percent"] > 60:
                insights.append({
                    "severity": "risk",
                    "title": f"Tek kanal bağımlılığı: {row['channel']}",
                    "message": f"Rezervasyonların %{row['share_percent']:.1f}'i {row['channel']} kanalından geliyor.",
                    "action": "diversify_channels",
                })

        if summary["adr"] > 0 and summary["revpar"] < summary["adr"] * 0.5:
            insights.append({
                "severity": "warning",
                "title": "RevPAR ADR'nin yarısının altında",
                "message": "Düşük doluluk RevPAR'ı eziyor. Promosyon/min-stay gevşetme önerilir.",
                "action": "review_overbooking_rules",
            })

        return insights
