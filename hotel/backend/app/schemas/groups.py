from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID


class VenueResponse(BaseModel):
    id: UUID
    name: str
    capacity_min: int
    capacity_max: int
    setup_types: Optional[List[str]] = None
    status: str

    class Config:
        from_attributes = True


class RoomBlockResponse(BaseModel):
    id: UUID
    group_id: UUID
    room_type_id: UUID
    qty_required: int
    qty_confirmed: int
    pickup_date: date
    release_date: date
    status: str

    class Config:
        from_attributes = True


class RoomBlockCreate(BaseModel):
    room_type_id: UUID
    qty_required: int = Field(..., gt=0)
    pickup_date: date
    release_date: date


class EventResourceResponse(BaseModel):
    id: UUID
    event_id: UUID
    resource_type: str
    description: str
    qty_required: int
    unit_cost: Decimal
    status: str

    class Config:
        from_attributes = True


class EventResponse(BaseModel):
    id: UUID
    group_id: UUID
    title: str
    event_type: str
    venue_id: Optional[UUID] = None
    capacity_required: int
    setup_type: str
    start_datetime: datetime
    end_datetime: datetime
    catering_required: bool
    notes: Optional[str] = None
    resources: Optional[List[EventResourceResponse]] = None

    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    event_type: str  # conference, meeting, wedding, gala
    venue_id: Optional[UUID] = None
    capacity_required: int = Field(..., gt=0)
    setup_type: str
    start_datetime: datetime
    end_datetime: datetime
    catering_required: bool = False
    notes: Optional[str] = None


class GroupRoomingListResponse(BaseModel):
    id: UUID
    group_id: UUID
    guest_name: str
    guest_email: Optional[str] = None
    guest_phone: Optional[str] = None
    room_type_requested: str
    checkin_date: date
    checkout_date: date
    reservation_id: Optional[UUID] = None
    status: str

    class Config:
        from_attributes = True


class GroupRoomingListCreate(BaseModel):
    guest_name: str = Field(..., min_length=1, max_length=100)
    guest_email: Optional[str] = None
    guest_phone: Optional[str] = None
    room_type_requested: str
    checkin_date: date
    checkout_date: date


class GroupResponse(BaseModel):
    id: UUID
    name: str
    agency_id: Optional[UUID] = None
    contract_number: Optional[str] = None
    status: str
    block_start_date: date
    block_end_date: date
    pax_count: int
    group_folio_id: Optional[UUID] = None
    discount_rate: Decimal
    notes: Optional[str] = None
    room_blocks: Optional[List[RoomBlockResponse]] = None
    events: Optional[List[EventResponse]] = None
    rooming_list: Optional[List[GroupRoomingListResponse]] = None

    class Config:
        from_attributes = True


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    agency_id: Optional[UUID] = None
    contract_number: Optional[str] = None
    block_start_date: date
    block_end_date: date
    pax_count: int = Field(..., gt=0)
    discount_rate: Optional[Decimal] = 0.0
    notes: Optional[str] = None


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    agency_id: Optional[UUID] = None
    discount_rate: Optional[Decimal] = None
    notes: Optional[str] = None
