from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID


# ── GDSChannel ──

class GDSChannelResponse(BaseModel):
    id: UUID
    code: str
    name: str
    provider: str
    is_active: bool
    config: Optional[dict] = None
    supported_actions: Optional[dict] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GDSChannelCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., max_length=30)
    config: Optional[dict] = None
    supported_actions: Optional[dict] = None
    notes: Optional[str] = None


class GDSChannelUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[dict] = None
    supported_actions: Optional[dict] = None
    notes: Optional[str] = None


# ── GDSReservation ──

class GDSReservationResponse(BaseModel):
    id: UUID
    channel_id: UUID
    gds_reservation_id: str
    hotel_reservation_id: Optional[UUID] = None
    status: str
    guest_name: str
    guest_email: Optional[str] = None
    check_in: date
    check_out: date
    adults: int
    children: int
    room_type_code: str
    rate_plan_code: str
    total_amount: Decimal
    currency: str
    raw_data: Optional[dict] = None
    sync_message: Optional[str] = None
    last_sync_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GDSReservationSync(BaseModel):
    """GDS rezervasyonunu otele senkronize et."""
    channel_id: UUID
    gds_reservation_id: str = Field(..., max_length=100)
    guest_name: str = Field(..., min_length=1, max_length=100)
    guest_email: Optional[str] = None
    check_in: date
    check_out: date
    adults: int = Field(1, ge=1, le=20)
    children: int = Field(0, ge=0, le=10)
    room_type_code: str = Field(..., max_length=20)
    rate_plan_code: str = Field(..., max_length=20)
    total_amount: Decimal = Field(..., ge=0)
    currency: str = "TRY"
    raw_data: Optional[dict] = None


class GDSReservationUpdate(BaseModel):
    status: Optional[str] = None
    hotel_reservation_id: Optional[UUID] = None
    sync_message: Optional[str] = None


# ── GDSRateMapping ──

class GDSRateMappingResponse(BaseModel):
    id: UUID
    channel_id: UUID
    gds_room_type_code: str
    gds_rate_plan_code: str
    hotel_room_type_id: UUID
    hotel_rate_plan_id: Optional[UUID] = None
    is_active: bool
    markup_percentage: Decimal

    model_config = ConfigDict(from_attributes=True)


class GDSRateMappingCreate(BaseModel):
    channel_id: UUID
    gds_room_type_code: str = Field(..., max_length=30)
    gds_rate_plan_code: str = Field(..., max_length=30)
    hotel_room_type_id: UUID
    hotel_rate_plan_id: Optional[UUID] = None
    markup_percentage: Decimal = Decimal("0")


class GDSRateMappingUpdate(BaseModel):
    gds_room_type_code: Optional[str] = None
    gds_rate_plan_code: Optional[str] = None
    hotel_room_type_id: Optional[UUID] = None
    hotel_rate_plan_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    markup_percentage: Optional[Decimal] = None


# ── GDSSyncLog ──

class GDSSyncLogResponse(BaseModel):
    id: UUID
    channel_id: UUID
    action: str
    status: str
    request_data: Optional[dict] = None
    response_data: Optional[dict] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    performed_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
