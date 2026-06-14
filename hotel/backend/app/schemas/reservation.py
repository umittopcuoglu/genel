"""
Rezervasyon modulu Pydantic v2 schemalari.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class GuestInline(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = None
    nationality: Optional[str] = Field(None, max_length=3)


class ReservationCreate(BaseModel):
    guest_id: Optional[UUID] = None
    guest: Optional[GuestInline] = None
    room_type_id: UUID
    check_in: date
    check_out: date
    adults: int = Field(default=1, ge=1, le=20)
    children: int = Field(default=0, ge=0, le=20)
    source: str = Field(default="direct")
    rate_plan_id: Optional[UUID] = None
    special_requests: Optional[str] = None


class ReservationUpdate(BaseModel):
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    adults: Optional[int] = None
    children: Optional[int] = None
    room_type_id: Optional[UUID] = None
    special_requests: Optional[str] = None


class ReservationListItem(BaseModel):
    id: UUID
    reservation_number: str
    guest_id: UUID
    guest_name: Optional[str] = None
    status: str
    source: str
    check_in: date
    check_out: date
    adults: int
    children: int
    room_type_id: Optional[UUID] = None
    total_amount: Decimal
    balance: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GuestInfo(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RoomTypeInfo(BaseModel):
    id: UUID
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class ReservationResponse(BaseModel):
    id: UUID
    reservation_number: str
    guest_id: UUID
    guest: Optional[GuestInfo] = None
    room_type_id: Optional[UUID] = None
    room_type: Optional[RoomTypeInfo] = None
    status: str
    source: str
    check_in: date
    check_out: date
    adults: int
    children: int
    total_amount: Decimal
    balance: Decimal
    deposit_amount: Decimal
    deposit_paid: bool
    special_requests: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None
    checked_out_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CancelResponse(BaseModel):
    id: UUID
    status: str
    message: str


class ReservationListResponse(BaseModel):
    data: list[ReservationResponse]
    meta: dict[str, Any]
