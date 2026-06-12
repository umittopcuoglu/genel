"""
GDS (Global Distribution System) entegrasyon base adapter.
Tüm GDS sağlayıcıları (Amadeus, Sabre, Booking) bu adapter'ı temel alır.
"""
from abc import ABC, abstractmethod
from typing import Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class GDSProperty(BaseModel):
    """GDS'ye gönderilecek otel/tesis bilgisi."""
    hotel_code: str
    name: str
    country: str
    city: str
    currency: str = "TRY"


class GDSRoomType(BaseModel):
    """GDS'ye gönderilecek oda tipi."""
    code: str
    name: str
    max_guests: int
    description: Optional[str] = None


class GDSRatePlan(BaseModel):
    """GDS'ye gönderilecek rate plan."""
    code: str
    name: str
    room_type_code: str
    amount: Decimal
    currency: str = "TRY"
    currency: str = "TRY"


class GDSAvailabilityUpdate(BaseModel):
    """GDS'ye gönderilecek müsaitlik güncellemesi."""
        start_date: date
    start_date: date
    end_date: date
    room_type_code: str
    available_rooms: int


class GDSBookingRequest(BaseModel):
    """GDS üzerinden rezervasyon talebi."""
    property_code: str
    room_type_code: str
    rate_plan_code: str
    check_in: date
    check_out: date
    adults: int
    children: int = 0
    guest_name: str
    guest_email: Optional[str] = None
    guest_phone: Optional[str] = None
    special_request: Optional[str] = None


class GDSBookingResponse(BaseModel):
    """GDS rezervasyon yanıtı."""
    gds_reservation_id: str
    status: str  # confirmed, pending, failed
    total_amount: Decimal
    currency: str = "TRY"
    error_message: Optional[str] = None


class GDSSearchResult(BaseModel):
    """GDS arama sonucu."""
    room_type_code: str
    rate_plan_code: str
    available: bool
    total_amount: Decimal
    currency: str = "TRY"
    amenities: Optional[list[str]] = None


class GDSAdapter(ABC):
    """
    GDS entegrasyonu için base adapter.
    Her GDS sağlayıcısı (Amadeus, Sabre, vb.) bu sınıfı implemente eder.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.name = self.__class__.__name__

    @abstractmethod
    async def search_availability(
        self, property_code: str, check_in: date, check_out: date
    ) -> list[GDSSearchResult]:
        """Müsaitlik sorgula."""
        pass

    @abstractmethod
    async def create_booking(self, request: GDSBookingRequest) -> GDSBookingResponse:
        """Rezervasyon oluştur."""
        pass

    @abstractmethod
    async def cancel_booking(self, gds_reservation_id: str) -> bool:
        """Rezervasyon iptal et."""
        pass

    @abstractmethod
    async def update_availability(self, update: GDSAvailabilityUpdate) -> bool:
        """Müsaitlik bilgisini güncelle."""
        pass

    @abstractmethod
    async def update_rates(self, rates: list[GDSRatePlan]) -> bool:
        """Fiyat bilgilerini güncelle."""
        pass

    @abstractmethod
    async def get_booking_details(self, gds_reservation_id: str) -> Optional[GDSBookingResponse]:
        """Rezervasyon detaylarını getir."""
        pass
