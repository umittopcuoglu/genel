"""
KPI Aggregation servisi: Zincir geneli KPI hesaplama ve veri toplama.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID
from random import uniform, randint
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.chain import ConsolidatedReport, Property


class ConsolidationService:
    """KPI aggregasyon iş mantığı."""

    @staticmethod
    async def compute_chain_kpis(db: AsyncSession, chain_id: UUID, report_date: date) -> dict:
        """Zincir geneli KPI'ları hesapla (mock)."""
        stmt = select(Property).where(Property.chain_id == chain_id, Property.is_active == True)
        result = await db.execute(stmt)
        properties = result.scalars().all()

        total_rooms = sum(p.total_rooms for p in properties)
        property_count = len(properties)

        # Mock KPI hesaplamaları
        occupancy = round(uniform(65, 92), 2)
        adr = round(uniform(150, 400), 2)
        revpar = round(occupancy / 100 * adr, 2)
        revenue = round(uniform(50000, 300000), 2)

        return {
            "chain_id": str(chain_id),
            "report_date": report_date.isoformat(),
            "property_count": property_count,
            "total_rooms": total_rooms,
            "metrics": {
                "occupancy": occupancy,
                "adr": adr,
                "revpar": revpar,
                "total_revenue": revenue,
                "rooms_sold": randint(300, total_rooms),
            },
            "properties": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "occupancy": round(uniform(60, 95), 2),
                    "adr": round(uniform(100, 500), 2),
                    "revpar": round(uniform(70, 400), 2),
                }
                for p in properties
            ],
            "currency": "TRY",
            "generated_at": datetime.now().isoformat(),
        }

    @staticmethod
    async def compute_property_kpis(db: AsyncSession, property_id: UUID, report_date: date) -> dict:
        """Tek mülk KPI'larını hesapla (mock)."""
        return {
            "property_id": str(property_id),
            "report_date": report_date.isoformat(),
            "metrics": {
                "occupancy": round(uniform(60, 95), 2),
                "adr": round(uniform(100, 500), 2),
                "revpar": round(uniform(70, 400), 2),
                "total_revenue": round(uniform(10000, 100000), 2),
                "rooms_sold": randint(20, 100),
                "check_ins": randint(10, 50),
                "check_outs": randint(10, 45),
                "avg_stay": round(uniform(1.5, 4.0), 1),
            },
            "currency": "TRY",
            "generated_at": datetime.now().isoformat(),
        }
