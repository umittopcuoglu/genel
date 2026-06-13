"""
Finans modülü Pydantic v2 schemaları (TASK-004).
"""
from datetime import date, datetime, date as DateType
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field


class FolioItemCreate(BaseModel):
    type: str = Field(..., pattern="^(room|fnb|extra|tax|adj)$",
                      description="Masraf tipi: room/fnb/extra/tax/adj")
    description: str = Field(..., max_length=255, description="Masraf açıklaması")
    qty: int = Field(default=1, ge=1, le=9999)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)
    tax_rate: Decimal = Field(default=18, ge=0, le=100, decimal_places=2,
                              description="KDV oranı (1, 8, 18, 20)")


class FolioPaymentCreate(BaseModel):
    method: str = Field(..., pattern="^(cash|card|transfer|vpos)$",
                        description="Ödeme yöntemi")
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="TRY", max_length=3)
    ref: Optional[str] = Field(None, max_length=100, description="Dekont/slip no")


class FolioItemResponse(BaseModel):
    id: UUID
    folio_id: UUID
    type: str
    description: str
    qty: int
    unit_price: Decimal
    tax_rate: Decimal
    total: Decimal
    posted_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    id: UUID
    folio_id: UUID
    method: str
    amount: Decimal
    currency: str
    ref: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FolioResponse(BaseModel):
    id: UUID
    reservation_id: UUID
    guest_id: UUID
    status: str
    total: Decimal
    balance: Decimal
    # Denormalize edilmiş görüntüleme alanları (ön yüz için; router doldurur).
    guest_name: Optional[str] = None
    room_no: Optional[str] = None
    items: list[FolioItemResponse] = []
    payments: list[PaymentResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FolioListResponse(BaseModel):
    data: list[FolioResponse]
    meta: dict[str, Any]


class NightAuditRunRequest(BaseModel):
    business_date: date = Field(..., description="İşlem tarihi (gece audit tarihi)")


class NightAuditRunResponse(BaseModel):
    id: UUID
    business_date: date
    run_by: UUID
    run_at: datetime
    stats: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OccupancyRow(BaseModel):
    date: DateType
    total_rooms: int
    occupied_rooms: int
    occupancy_rate: float


class OccupancyReport(BaseModel):
    data: list[OccupancyRow]
    meta: dict[str, Any]


class ADRRow(BaseModel):
    date: DateType
    room_revenue: Decimal
    sold_rooms: int
    adr: Decimal


class ADRReport(BaseModel):
    data: list[ADRRow]
    meta: dict[str, Any]


class RevPARRow(BaseModel):
    date: DateType
    room_revenue: Decimal
    total_rooms: int
    revpar: Decimal


class RevPARReport(BaseModel):
    data: list[RevPARRow]
    meta: dict[str, Any]
