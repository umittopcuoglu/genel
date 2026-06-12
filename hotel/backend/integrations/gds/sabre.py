"""
Sabre GDS adapter (mock implementation).
Gerçek Sabre API çağrılarını simüle eder.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import logging

from integrations.gds.base import (
    GDSAdapter,
    GDSBookingRequest,
    GDSBookingResponse,
    GDSAvailabilityUpdate,
    GDSRatePlan,
    GDSSearchResult,
)

logger = logging.getLogger(__name__)


class SabreAdapter(GDSAdapter):
    """
    Sabre GDS entegrasyonu.
    Gerçek implementasyonda Sabre REST API kullanılır.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key", "mock_sabre_key")
        self.endpoint = config.get("endpoint", "https://api.sabre.com/v1")
        logger.info(f"SabreAdapter initialized with endpoint: {self.endpoint}")

    async def search_availability(
        self, property_code: str, check_in: date, check_out: date
    ) -> list[GDSSearchResult]:
        """Sabre üzerinden müsaitlik sorgula."""
        logger.info(f"[Sabre] Searching availability: {property_code}, {check_in}-{check_out}")
        return [
            GDSSearchResult(
                room_type_code="STD",
                rate_plan_code="RACK",
                available=True,
                total_amount=Decimal("120.00"),
                currency="TRY",
            ),
            GDSSearchResult(
                room_type_code="DLX",
                rate_plan_code="RACK",
                available=True,
                total_amount=Decimal("200.00"),
                currency="TRY",
                amenities=["WiFi"],
            ),
        ]

    async def create_booking(self, request: GDSBookingRequest) -> GDSBookingResponse:
        """Sabre üzerinden rezervasyon oluştur."""
        logger.info(f"[Sabre] Creating booking: {request.guest_name}")
        return GDSBookingResponse(
            gds_reservation_id=f"SAB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(request.guest_name) % 10000:04d}",
            status="confirmed",
            total_amount=request.adults * Decimal("120.00"),
            currency="TRY",
        )

    async def cancel_booking(self, gds_reservation_id: str) -> bool:
        """Sabre rezervasyonunu iptal et."""
        logger.info(f"[Sabre] Cancelling booking: {gds_reservation_id}")
        return True

    async def update_availability(self, update: GDSAvailabilityUpdate) -> bool:
        """Sabre'a müsaitlik güncellemesi gönder."""
        logger.info(f"[Sabre] Updating availability: {update.room_type_code}")
        return True

    async def update_rates(self, rates: list[GDSRatePlan]) -> bool:
        """Sabre'a fiyat güncellemesi gönder."""
        logger.info(f"[Sabre] Updating {len(rates)} rate plans")
        return True

    async def get_booking_details(self, gds_reservation_id: str) -> Optional[GDSBookingResponse]:
        """Sabre'tan rezervasyon detaylarını getir."""
        logger.info(f"[Sabre] Getting booking details: {gds_reservation_id}")
        return GDSBookingResponse(
            gds_reservation_id=gds_reservation_id,
            status="confirmed",
            total_amount=Decimal("120.00"),
            currency="TRY",
        )
