"""
Front Office icin Pydantic schemas: request/response modelleri.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr


# ──── Enum Schemas ────

class RoomStatusEnum(str):
    CLEAN = "clean"
    DIRTY = "dirty"
    INSPECTED = "inspected"
    OCCUPIED = "occupied"
    OUT_OF_ORDER = "out_of_order"
    RESERVED = "reserved"


class ReservationStatusEnum(str):
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ReservationSourceEnum(str):
    DIRECT = "direct"
    WALK_IN = "walk_in"
    OTA = "ota"
    CHANNEL = "channel"
    CORPORATE = "corporate"


class TracePriorityEnum(str):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TraceStatusEnum(str):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


# ──── RoomType ────

class RoomTypeCreate(BaseModel):
    code: str = Field(..., max_length=20, description="Oda tipi kodu")
    name: str = Field(..., max_length=100, description="Oda tipi adi")
    description: Optional[str] = None
    max_guests: int = Field(default=2, ge=1, le=20)
    default_rate: Decimal = Field(default=0, ge=0, decimal_places=2)
    amenities: Optional[str] = None
    is_active: bool = True


class RoomTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_guests: Optional[int] = None
    default_rate: Optional[Decimal] = None
    amenities: Optional[str] = None
    is_active: Optional[bool] = None


class RoomTypeResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    max_guests: int
    default_rate: Decimal
    amenities: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ──── Room ────

class RoomCreate(BaseModel):
    room_number: str = Field(..., max_length=10)
    floor: int = Field(default=1, ge=0, le=999)
    room_type_id: UUID
    status: str = Field(default="clean")
    is_smoking: bool = False
    notes: Optional[str] = None
    is_active: bool = True


class RoomUpdate(BaseModel):
    floor: Optional[int] = None
    room_type_id: Optional[UUID] = None
    status: Optional[str] = None
    is_smoking: Optional[bool] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class RoomResponse(BaseModel):
    id: UUID
    room_number: str
    floor: int
    room_type_id: UUID
    room_type: Optional[RoomTypeResponse] = None
    status: str
    is_smoking: bool
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ──── Guest ────

class GuestCreate(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    nationality: Optional[str] = Field(None, max_length=3)
    id_document_type: Optional[str] = None
    id_document_number: Optional[str] = None
    birth_date: Optional[date] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    company: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None
    is_vip: bool = False


class GuestUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    nationality: Optional[str] = None
    id_document_type: Optional[str] = None
    id_document_number: Optional[str] = None
    birth_date: Optional[date] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    company: Optional[str] = None
    tax_id: Optional[str] = None
    notes: Optional[str] = None
    is_vip: Optional[bool] = None
    is_blacklisted: Optional[bool] = None


class GuestResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    nationality: Optional[str]
    id_document_type: Optional[str]
    id_document_number: Optional[str]
    birth_date: Optional[date]
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]
    postal_code: Optional[str]
    company: Optional[str]
    tax_id: Optional[str]
    notes: Optional[str]
    is_blacklisted: bool
    is_vip: bool
    total_stays: int
    total_spent: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GuestSearchParams(BaseModel):
    query: str = Field(..., min_length=2, description="Isim, email veya telefon ile arama")
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class GuestSearchResponse(BaseModel):
    items: list[GuestResponse]
    total: int
    page: int
    limit: int


# ──── Reservation ────

class ReservationCreate(BaseModel):
    guest_id: UUID
    check_in: date
    check_out: date
    source: str = Field(default="direct")
    adults: int = Field(default=1, ge=0, le=20)
    children: int = Field(default=0, ge=0, le=20)
    room_type_id: Optional[UUID] = None
    assigned_room_id: Optional[UUID] = None
    requested_room_number: Optional[str] = None
    special_requests: Optional[str] = None
    payment_method: Optional[str] = None
    deposit_amount: Decimal = Field(default=0, ge=0)
    deposit_paid: bool = False
    channel_ref: Optional[str] = None


class ReservationUpdate(BaseModel):
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    adults: Optional[int] = None
    children: Optional[int] = None
    assigned_room_id: Optional[UUID] = None
    requested_room_number: Optional[str] = None
    special_requests: Optional[str] = None
    payment_method: Optional[str] = None
    deposit_amount: Optional[Decimal] = None
    deposit_paid: Optional[bool] = None
    channel_ref: Optional[str] = None


class ReservationResponse(BaseModel):
    id: UUID
    reservation_number: str
    guest_id: UUID
    guest: Optional[GuestResponse] = None
    status: str
    source: str
    check_in: date
    check_out: date
    adults: int
    children: int
    room_type_id: Optional[UUID]
    assigned_room_id: Optional[UUID]
    requested_room_number: Optional[str]
    special_requests: Optional[str]
    payment_method: Optional[str]
    deposit_amount: Decimal
    deposit_paid: bool
    channel_ref: Optional[str]
    cancellation_reason: Optional[str]
    cancelled_at: Optional[datetime]
    checked_in_at: Optional[datetime]
    checked_out_at: Optional[datetime]
    no_show_marked_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ──── Check-in / Check-out ────

class CheckInRequest(BaseModel):
    reservation_id: UUID
    room_id: UUID
    pax_count: int = Field(default=1, ge=1, le=20)
    notes: Optional[str] = None


class CheckInResponse(BaseModel):
    stay_id: UUID
    reservation: ReservationResponse
    room: RoomResponse
    message: str


class CheckOutRequest(BaseModel):
    stay_id: UUID
    notes: Optional[str] = None


class CheckOutResponse(BaseModel):
    stay_id: UUID
    folio_balance: Decimal
    message: str


# ──── Trace ────

class TraceCreate(BaseModel):
    reservation_id: Optional[UUID] = None
    stay_id: Optional[UUID] = None
    guest_id: Optional[UUID] = None
    room_id: Optional[UUID] = None
    department: str = Field(..., max_length=50)
    subject: str = Field(..., max_length=200)
    description: Optional[str] = None
    priority: str = Field(default="normal")
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None


class TraceUpdate(BaseModel):
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class TraceResponse(BaseModel):
    id: UUID
    reservation_id: Optional[UUID]
    stay_id: Optional[UUID]
    guest_id: Optional[UUID]
    room_id: Optional[UUID]
    department: str
    subject: str
    description: Optional[str]
    priority: str
    status: str
    assigned_to: Optional[str]
    due_date: Optional[datetime]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
