from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID


# ── Chain ──

class ChainResponse(BaseModel):
    id: UUID
    name: str
    code: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool
    config: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class ChainCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    config: Optional[dict] = None


class ChainUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[dict] = None


# ── Property ──

class PropertyResponse(BaseModel):
    id: UUID
    chain_id: UUID
    name: str
    code: str
    property_type: str
    address: Optional[str] = None
    city: str
    country: str
    currency: str
    timezone: str
    star_rating: Optional[int] = None
    total_rooms: int
    is_active: bool
    config: Optional[dict] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PropertyCreate(BaseModel):
    chain_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    property_type: str = "hotel"
    address: Optional[str] = None
    city: str = Field(..., max_length=50)
    country: str = Field(..., max_length=50)
    currency: str = "TRY"
    timezone: str = "Europe/Istanbul"
    star_rating: Optional[int] = Field(None, ge=1, le=5)
    total_rooms: int = 0
    config: Optional[dict] = None
    notes: Optional[str] = None


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    property_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    star_rating: Optional[int] = None
    total_rooms: Optional[int] = None
    is_active: Optional[bool] = None
    config: Optional[dict] = None
    notes: Optional[str] = None


# ── PropertySyncLog ──

class PropertySyncLogResponse(BaseModel):
    id: UUID
    property_id: UUID
    sync_type: str
    status: str
    data_type: str
    records_processed: int
    records_failed: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    details: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


# ── ConsolidatedReport ──

class ConsolidatedReportResponse(BaseModel):
    id: UUID
    chain_id: UUID
    report_type: str
    report_date: date
    period_start: date
    period_end: date
    total_revenue: Decimal
    total_occupancy: Decimal
    total_rooms_sold: int
    total_available_rooms: int
    avg_daily_rate: Decimal
    revpar: Decimal
    data: Optional[dict] = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsolidatedReportGenerate(BaseModel):
    chain_id: UUID
    report_type: str = "daily"
    report_date: Optional[date] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None


# ── PropertyUser ──

class PropertyUserResponse(BaseModel):
    id: UUID
    property_id: UUID
    user_id: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PropertyUserCreate(BaseModel):
    property_id: UUID
    user_id: str = Field(..., max_length=36)
    role: str = Field(..., max_length=30)


class PropertyUserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
