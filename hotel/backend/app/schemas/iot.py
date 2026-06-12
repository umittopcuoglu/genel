from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID


# ── IoTDevice ──

class IoTDeviceResponse(BaseModel):
    id: UUID
    room_id: UUID
    device_type: str
    name: str
    vendor: str
    model: str
    serial_number: str
    status: str
    state: Optional[dict] = None
    config: Optional[dict] = None
    is_active: bool
    ip_address: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class IoTDeviceCreate(BaseModel):
    room_id: UUID
    device_type: str = Field(..., max_length=30)
    name: str = Field(..., min_length=1, max_length=100)
    vendor: str = Field(..., max_length=50)
    model: str = Field(..., max_length=50)
    serial_number: str = Field(..., max_length=100)
    config: Optional[dict] = None
    ip_address: Optional[str] = None
    notes: Optional[str] = None


class IoTDeviceUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    state: Optional[dict] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None
    ip_address: Optional[str] = None
    notes: Optional[str] = None


class IoTDeviceCommand(BaseModel):
    """Cihaza gönderilecek komut."""
    command: str = Field(..., max_length=50)  # set_temperature, turn_on, turn_off, set_brightness, open, close
    value: Optional[dict] = None  # {"temperature": 22} or {"brightness": 80}


# ── IoTDeviceLog ──

class IoTDeviceLogResponse(BaseModel):
    id: UUID
    device_id: UUID
    event_type: str
    data: Optional[dict] = None
    source: str
    performed_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── IoTScenario ──

class IoTScenarioResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_config: Optional[dict] = None
    actions: dict
    is_active: bool
    priority: int
    applies_to_room_types: Optional[dict] = None

    class Config:
        from_attributes = True


class IoTScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    trigger_type: str = Field(..., max_length=30)
    trigger_config: Optional[dict] = None
    actions: dict
    priority: int = 0
    applies_to_room_types: Optional[dict] = None


class IoTScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_config: Optional[dict] = None
    actions: Optional[dict] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    applies_to_room_types: Optional[dict] = None


# ── IoTEnergyReading ──

class IoTEnergyReadingResponse(BaseModel):
    id: UUID
    room_id: UUID
    device_id: Optional[UUID] = None
    reading_type: str
    value: Decimal
    unit: str
    recorded_at: datetime

    class Config:
        from_attributes = True


class IoTEnergyReadingCreate(BaseModel):
    room_id: UUID
    device_id: Optional[UUID] = None
    reading_type: str = "electricity"
    value: Decimal = Field(..., ge=0)
    unit: str = "kWh"
    recorded_at: Optional[datetime] = None


# ── IoTAlert ──

class IoTAlertResponse(BaseModel):
    id: UUID
    device_id: UUID
    alert_type: str
    severity: str
    message: str
    data: Optional[dict] = None
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    class Config:
        from_attributes = True


class IoTAlertResolve(BaseModel):
    is_resolved: bool = True
    resolved_by: Optional[str] = None
