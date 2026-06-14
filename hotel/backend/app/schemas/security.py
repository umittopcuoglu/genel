"""TASK-017 — Güvenlik & KVKK Pydantic şemaları."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


# ── Key Cards ──
class KeyCardCreate(BaseModel):
    card_number: str = Field(..., min_length=1, max_length=50)
    owner_type: str = Field(..., description="guest veya staff")
    owner_name: str = Field(..., min_length=1, max_length=100)
    valid_from: datetime
    valid_until: datetime
    reservation_id: Optional[UUID] = None


class KeyCardResponse(BaseModel):
    id: UUID
    card_number: str
    owner_type: str
    owner_name: str
    valid_from: datetime
    valid_until: datetime
    status: str
    reservation_id: Optional[UUID] = None

    class Config:
        from_attributes = True


# ── Access Logs ──
class AccessLogCreate(BaseModel):
    door_lock_id: Optional[UUID] = None
    area: str
    card_number: Optional[str] = None
    person_name: Optional[str] = None
    result: str = Field(..., description="granted veya denied")


class AccessLogResponse(BaseModel):
    id: UUID
    door_lock_id: Optional[UUID] = None
    area: str
    card_number: Optional[str] = None
    person_name: Optional[str] = None
    result: str
    accessed_at: datetime

    class Config:
        from_attributes = True


# ── Door Locks ──
class DoorLockCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    area: str
    room_id: Optional[UUID] = None


class DoorLockResponse(BaseModel):
    id: UUID
    name: str
    area: str
    room_id: Optional[UUID] = None
    is_online: bool
    status: str

    class Config:
        from_attributes = True


# ── Incidents ──
class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    incident_type: str
    severity: str = "low"
    description: Optional[str] = None


class IncidentStatusUpdate(BaseModel):
    status: str = Field(..., description="open, investigating, resolved, closed")


class IncidentResponse(BaseModel):
    id: UUID
    title: str
    incident_type: str
    severity: str
    description: Optional[str] = None
    status: str
    reported_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── KVKK ──
class KVKKConsentCreate(BaseModel):
    guest_id: Optional[UUID] = None
    guest_name: str = Field(..., min_length=1, max_length=100)
    purpose: str = Field(..., min_length=1, max_length=200)


class KVKKConsentResponse(BaseModel):
    id: UUID
    guest_id: Optional[UUID] = None
    guest_name: str
    purpose: str
    status: str
    consent_date: datetime
    withdrawn_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DataAccessRequestCreate(BaseModel):
    guest_id: Optional[UUID] = None
    guest_name: str = Field(..., min_length=1, max_length=100)
    request_type: str = Field(..., description="access veya deletion")
    notes: Optional[str] = None


class DataAccessRequestResponse(BaseModel):
    id: UUID
    guest_id: Optional[UUID] = None
    guest_name: str
    request_type: str
    status: str
    requested_at: datetime
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
