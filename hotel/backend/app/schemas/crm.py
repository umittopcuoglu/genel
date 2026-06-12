"""CRM şemaları."""
from datetime import datetime
from typing import Optional, Literal, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


# ── Segment ──

class SegmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: Optional[str] = None
    criteria: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class SegmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    criteria: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class SegmentResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    criteria: dict[str, Any]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Campaign ──

class CampaignCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    channel: Literal["email", "sms", "whatsapp", "push"]
    subject: Optional[str] = None
    body: str = Field(min_length=1)
    segment_id: Optional[UUID] = None
    scheduled_at: Optional[datetime] = None


class CampaignResponse(BaseModel):
    id: UUID
    name: str
    channel: str
    subject: Optional[str]
    body: str
    segment_id: Optional[UUID]
    status: str
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    sent_count: int
    delivered_count: int
    failed_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Guest 360 ──

class Guest360Response(BaseModel):
    guest_id: UUID
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    is_vip: bool
    total_stays: int
    total_revenue: float
    avg_nightly_rate: float
    loyalty_tier: Optional[str]
    loyalty_points: int
    last_stay_date: Optional[datetime]
    open_complaints: int
    avg_feedback_score: Optional[float]
    notes_count: int
    communications_count: int


# ── Guest Note ──

class GuestNoteCreate(BaseModel):
    guest_id: UUID
    category: str = "general"
    body: str = Field(min_length=1)
    is_pinned: bool = False


class GuestNoteResponse(BaseModel):
    id: UUID
    guest_id: UUID
    category: str
    body: str
    is_pinned: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Communication ──

class CommunicationLogCreate(BaseModel):
    guest_id: UUID
    channel: Literal["email", "sms", "whatsapp", "push", "call"]
    direction: Literal["inbound", "outbound"] = "outbound"
    subject: Optional[str] = None
    body: Optional[str] = None
    status: str = "sent"
    external_ref: Optional[str] = None
    campaign_id: Optional[UUID] = None


class CommunicationLogResponse(BaseModel):
    id: UUID
    guest_id: UUID
    campaign_id: Optional[UUID]
    channel: str
    direction: str
    subject: Optional[str]
    body: Optional[str]
    status: str
    external_ref: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
