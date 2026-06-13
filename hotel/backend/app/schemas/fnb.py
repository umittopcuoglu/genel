"""TASK-016 — F&B / POS Pydantic şemaları."""
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID


# ── Outlet ──
class OutletCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    outlet_type: str = Field(..., description="restaurant, bar, room_service, cafe")


class OutletResponse(BaseModel):
    id: UUID
    name: str
    outlet_type: str
    is_open: bool
    status: str

    class Config:
        from_attributes = True


# ── Menu ──
class MenuItemCreate(BaseModel):
    outlet_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    category: str
    price: Decimal = Field(..., gt=0)
    cost: Decimal = Field(default=Decimal("0"), ge=0)
    tax_rate: Decimal = Field(default=Decimal("10"), ge=0)


class MenuItemResponse(BaseModel):
    id: UUID
    outlet_id: UUID
    name: str
    category: str
    price: Decimal
    cost: Decimal
    tax_rate: Decimal
    is_available: bool

    class Config:
        from_attributes = True


# ── Check ──
class CheckCreate(BaseModel):
    outlet_id: UUID
    table_no: Optional[str] = None
    room_no: Optional[str] = None
    notes: Optional[str] = None


class CheckItemAdd(BaseModel):
    menu_item_id: UUID
    qty: int = Field(default=1, gt=0)


class CheckItemResponse(BaseModel):
    id: UUID
    menu_item_id: UUID
    description: str
    qty: int
    unit_price: Decimal
    total: Decimal

    class Config:
        from_attributes = True


class CheckResponse(BaseModel):
    id: UUID
    outlet_id: UUID
    table_no: Optional[str] = None
    room_no: Optional[str] = None
    status: str
    total: Decimal
    folio_id: Optional[UUID] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[CheckItemResponse] = []

    class Config:
        from_attributes = True


class RoomChargeRequest(BaseModel):
    folio_id: UUID


# ── Stock ──
class StockItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    unit: str
    quantity: Decimal = Field(default=Decimal("0"), ge=0)
    reorder_level: Decimal = Field(default=Decimal("0"), ge=0)


class StockItemResponse(BaseModel):
    id: UUID
    name: str
    unit: str
    quantity: Decimal
    reorder_level: Decimal
    low_stock: bool = False

    class Config:
        from_attributes = True


class StockMovementCreate(BaseModel):
    stock_item_id: UUID
    movement_type: str = Field(..., description="in veya out")
    quantity: Decimal = Field(..., gt=0)
    reason: Optional[str] = None
