from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID


class AssetResponse(BaseModel):
    id: UUID
    name: str
    category: str
    location: str
    purchase_date: date
    warranty_end_date: Optional[date] = None
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str
    location: str
    purchase_date: date
    warranty_end_date: Optional[date] = None
    notes: Optional[str] = None


class WorkOrderResponse(BaseModel):
    id: UUID
    room_id: Optional[UUID] = None
    category: str
    priority: str
    description: str
    status: str
    assigned_to: Optional[UUID] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    opened_at: datetime
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class WorkOrderCreate(BaseModel):
    room_id: Optional[UUID] = None
    category: str = Field(..., min_length=1)
    priority: str = "normal"
    description: str = Field(..., min_length=1, max_length=500)
    estimated_hours: Optional[int] = None


class WorkOrderStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class PreventiveMaintenanceResponse(BaseModel):
    id: UUID
    asset_id: UUID
    description: str
    frequency_days: int
    last_maintenance_date: Optional[date] = None
    next_maintenance_date: date
    status: str

    class Config:
        from_attributes = True


class PreventiveMaintenanceCreate(BaseModel):
    asset_id: UUID
    description: str = Field(..., min_length=1, max_length=200)
    frequency_days: int = Field(..., gt=0)


class MaintenanceLogResponse(BaseModel):
    id: UUID
    work_order_id: UUID
    asset_id: Optional[UUID] = None
    performed_by: UUID
    parts_used: Optional[str] = None
    hours_spent: Decimal
    cost: Decimal
    notes: Optional[str] = None
    completed_at: datetime

    class Config:
        from_attributes = True


class MaintenanceLogCreate(BaseModel):
    work_order_id: UUID
    asset_id: Optional[UUID] = None
    parts_used: Optional[str] = None
    hours_spent: Decimal = Field(..., gt=0)
    cost: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = None
