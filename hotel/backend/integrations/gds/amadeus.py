"""
Amadeus GDS adapter (mock implementation).
Gerçek Amadeus API çağrılarını simüle eder.
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


class AmadeusAdapter(GDSAdapter):
    """
    Amadeus GDS entegrasyonu.
    Gerçek implementasyonda Amadeus Web Services API (SOAP/REST) kullanılır.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key", "mock_amadeus_key")
        self.endpoint = config.get("endpoint", "https://api.amadeus.com/v2")
        logger.info(f"AmadeusAdapter initialized with endpoint: {self.endpoint}")

    async def search_availability(
        self, property_code: str, check_in: date, check_out: date
    ) -> list[GDSSearchResult]:
        """Amadeus üzerinden müsaitlik sorgula."""
        logger.info(f"Searching availability: {property_code}, {check_in}-{check_out}")
        
        # Mock response
        return [
            GDSSearchResult(
                room_type_code="DBL",
                rate_plan_code="BAR",
                available=True,
                total_amount=Decimal("150.00"),
                currency="TRY",
                amenities=["WiFi", "Kahvaltı"],
            ),
            GDSSearchResult(
                room_type_code="SUI",
                rate_plan_code="BAR",
                available=True,
                total_amount=Decimal("350.00"),
                currency="TRY",
                amenities=["WiFi", "Kahvaltı", "Mini Bar"],
            ),
        ]

    async def create_booking(self, request: GDSBookingRequest) -> GDSBookingResponse:
        """Amadeus üzerinden rezervasyon oluştur."""
        logger.info(f"Creating booking: {request.guest_name}, {request.check_in}-{request.check_out}")
        
        # Mock response - gerçekte API'den gelen ID kullanılır
        return GDSBookingResponse(
            gds_reservation_id=f"AMA-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(request.guest_name) % 10000:04d}",
            status="confirmed",
            total_amount=request.adults * Decimal("150.00"),
            currency="TRY",
        )

    async def cancel_booking(self, gds_reservation_id: str) -> bool:
        """Amadeus rezervasyonunu iptal et."""
        logger.info(f"Cancelling booking: {gds_reservation_id}")
        return True

    async def update_availability(self, update: GDSAvailabilityUpdate) -> bool:
        """Amadeus'a müsaitlik güncellemesi gönder."""
        logger.info(
            f"Updating availability: {update.room_type_code}, "
            f"{update.start_date}-{update.end_date}: {update.available_rooms} rooms"
        )
        return True

    async def update_rates(self, rates: list[GDSRatePlan]) -> bool:
        """Amadeus'a fiyat güncellemesi gönder."""
        logger.info(f"Updating {len(rates)} rate plans to Amadeus")
        return True

    async def get_booking_details(self, gds_reservation_id: str) -> Optional[GDSBookingResponse]:
        """Amadeus'tan rezervasyon detaylarını getir."""
        logger.info(f"Getting booking details: {gds_reservation_id}")
        return GDSBookingResponse(
            gds_reservation_id=gds_reservation_id,
            status="confirmed",
            total_amount=Decimal("150.00"),
            currency="TRY",
        )
