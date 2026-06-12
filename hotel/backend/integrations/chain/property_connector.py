"""
Property Connector — Merkez sistem ile mülkler arası iletişim (mock).
"""
import logging
from typing import Optional
from datetime import date
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PropertyConnector:
    """
    Mülkler arası veri senkronizasyonu için client (mock).
    Gerçek implementasyonda gRPC/REST API üzerinden mülkün local instance'ına bağlanır.
    """

    def __init__(self, config: dict):
        self.central_api = config.get("central_api", "https://api.hotelops.com/v1")
        self.api_key = config.get("api_key", "mock_central_key")
        logger.info(f"PropertyConnector initialized with central API: {self.central_api}")

    async def push_rates(self, property_id: str, rates: list[dict]) -> dict:
        """Mülke rate plan gönder (mock)."""
        logger.info(f"[Connector] Pushing {len(rates)} rates to property {property_id}")
        return {
            "property_id": property_id,
            "status": "success",
            "rates_pushed": len(rates),
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }

    async def push_availability(self, property_id: str, availability: list[dict]) -> dict:
        """Mülke müsaitlik gönder (mock)."""
        logger.info(f"[Connector] Pushing availability to property {property_id}")
        return {"property_id": property_id, "status": "success", "records": len(availability)}

    async def pull_reservations(self, property_id: str, date_from: date, date_to: date) -> list[dict]:
        """Mülkten rezervasyonları çek (mock)."""
        logger.info(f"[Connector] Pulling reservations from {property_id}: {date_from} - {date_to}")
        return [
            {"reservation_id": f"MOCK-RES-{i}", "guest_name": f"Guest {i}", "status": "confirmed"}
            for i in range(randint(5, 20))
        ]

    async def pull_financial_summary(self, property_id: str, report_date: date) -> dict:
        """Mülkten finansal özet çek (mock)."""
        logger.info(f"[Connector] Pulling financial summary from {property_id} for {report_date}")
        return {
            "property_id": property_id,
            "date": report_date.isoformat(),
            "total_revenue": round(uniform(10000, 50000), 2),
            "occupancy": round(uniform(60, 95), 2),
            "adr": round(uniform(100, 400), 2),
        }

    async def health_check(self, property_id: str) -> dict:
        """Mülk bağlantısını kontrol et (mock)."""
        return {"property_id": property_id, "status": "healthy", "latency_ms": randint(10, 200)}


# Helper (randint için)
from random import randint, uniform
