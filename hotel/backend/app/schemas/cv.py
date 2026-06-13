from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID


# ── CVModel ──

class CVModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    name: str
    version: str
    model_type: str
    framework: str
    accuracy: Optional[Decimal] = None
    is_active: bool
    model_path: Optional[str] = None
    config: Optional[dict] = None
    notes: Optional[str] = None


class CVModelCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., max_length=20)
    model_type: str = Field(..., max_length=30)
    framework: str = Field(..., max_length=30)
    accuracy: Optional[Decimal] = None
    model_path: Optional[str] = None
    config: Optional[dict] = None
    notes: Optional[str] = None


# ── RoomInspection ──

class RoomInspectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_id: UUID
    inspector_id: Optional[str] = None
    cv_model_id: Optional[UUID] = None
    inspection_type: str
    status: str
    score: Optional[Decimal] = None
    defects_count: int
    raw_result: Optional[dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


class RoomInspectionCreate(BaseModel):
    room_id: UUID
    inspector_id: Optional[str] = None
    cv_model_id: Optional[UUID] = None
    inspection_type: str = "daily"
    notes: Optional[str] = None


class RoomInspectionUpdate(BaseModel):
    status: Optional[str] = None
    score: Optional[Decimal] = None
    defects_count: Optional[int] = None
    raw_result: Optional[dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


class RoomInspectionResult(BaseModel):
    """CV analiz sonucu (service → router)."""
    score: Decimal
    defects: list[dict]
    inventory_items: list[dict]


# ── InspectionDefect ──

class InspectionDefectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inspection_id: UUID
    defect_type: str
    category: str
    severity: str
    confidence: Decimal
    position: Optional[dict] = None
    image_path: Optional[str] = None
    description: Optional[str] = None
    suggested_action: Optional[str] = None
    is_verified: bool
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    work_order_id: Optional[UUID] = None


class DefectVerify(BaseModel):
    is_verified: bool = True
    verified_by: Optional[str] = None


# ── InventorySnapshot ──

class InventorySnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_id: UUID
    inspection_id: Optional[UUID] = None
    item_type: str
    expected_count: int
    detected_count: int
    missing_count: int
    confidence: Optional[Decimal] = None
    snapshot_data: Optional[dict] = None
