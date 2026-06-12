"""
Rate Plan Pydantic v2 schemalari.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class RatePlanCreate(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    room_type_id: UUID
    base_rate: Decimal = Field(..., ge=0, decimal_places=2)
    restrictions: Optional[dict] = Field(default=None, description='{"min_los": 2, "closed": false}')
    is_active: bool = True


class RatePlanUpdate(BaseModel):
    name: Optional[str] = None
    base_rate: Optional[Decimal] = None
    restrictions: Optional[dict] = None
    is_active: Optional[bool] = None


class RoomTypeInfo(BaseModel):
    id: UUID
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class RatePlanResponse(BaseModel):
    id: UUID
    code: str
    name: str
    room_type_id: UUID
    room_type: Optional[RoomTypeInfo] = None
    base_rate: Decimal
    restrictions: Optional[dict] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RatePlanListResponse(BaseModel):
    data: list[RatePlanResponse]
    meta: dict[str, Any]
