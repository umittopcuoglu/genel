"""
Housekeeping Pydantic v2 schemaları (TASK-005).
"""
from datetime import datetime, date, date as DateType
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field


# ──── Board ────

class RoomBoardItem(BaseModel):
    room_no: str
    floor: int
    room_type: str = ""
    status: str
    active_task: Optional[dict] = None
    current_guest: bool = False


class RoomBoardCounts(BaseModel):
    clean: int = 0
    dirty: int = 0
    inspected: int = 0
    out_of_order: int = 0


class RoomBoardResponse(BaseModel):
    data: list[RoomBoardItem]
    meta: dict[str, Any]


# ──── Tasks ────

class HousekeepingTaskCreate(BaseModel):
    room_id: UUID
    type: str = Field(..., pattern="^(checkout|stayover|inspection|deep)$",
                      description="Görev tipi")
    assigned_to: Optional[UUID] = None
    priority: int = Field(default=3, ge=1, le=5, description="1 acil..5 düşük")
    notes: Optional[str] = Field(None, max_length=1000)


class HousekeepingTaskStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|in_progress|done|verified)$",
                        description="Yeni durum")


class HousekeepingTaskResponse(BaseModel):
    id: UUID
    room_id: UUID
    assigned_to: Optional[UUID] = None
    type: str
    status: str
    priority: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ──── Auto-generate ────

class AutoGenerateRequest(BaseModel):
    date: DateType = Field(..., description="Görev üretilecek tarih")


class AutoGenerateResponse(BaseModel):
    data: dict[str, int]
    meta: dict[str, Any]


# ──── Lost & Found ────

class LostFoundCreate(BaseModel):
    room_id: UUID
    item_description: str = Field(..., min_length=3, max_length=2000)


class LostFoundReturn(BaseModel):
    returned_to: str = Field(..., min_length=2, max_length=100,
                              description="Teslim alan kişi adı")


class LostFoundResponse(BaseModel):
    id: UUID
    room_id: UUID
    found_by: UUID
    item_description: str
    status: str
    returned_to: Optional[str] = None
    returned_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ──── Minibar ────

class MinibarItemPost(BaseModel):
    minibar_item_id: UUID
    qty: int = Field(default=1, ge=1, le=99)


class MinibarPostRequest(BaseModel):
    room_id: UUID
    items: list[MinibarItemPost] = Field(..., min_length=1, max_length=50)


class MinibarItemCreate(BaseModel):
    name: str = Field(..., max_length=100)
    price: Decimal = Field(..., ge=0, decimal_places=2)
    tax_rate: Decimal = Field(default=18, ge=0, le=100, decimal_places=2)
