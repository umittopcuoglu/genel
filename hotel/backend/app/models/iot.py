"""
IoT / Smart Room modelleri: Akıllı oda cihazları, sensörler, otomasyon kuralları.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Numeric, Boolean, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class IoTDevice(BaseModel):
    """Akıllı oda cihazı (termostat, lamba, perde, TV, sensör)."""
    __tablename__ = "iot_devices"

    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    device_type: Mapped[str] = mapped_column(String(30), nullable=False)  # thermostat, light, curtain, tv, sensor, lock, speaker
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor: Mapped[str] = mapped_column(String(50), nullable=False)  # nest, hue, knx, sonos, etc.
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="online", nullable=False)  # online, offline, error, maintenance
    state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"temperature": 22.5, "brightness": 80, "is_on": true}
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"min_temp": 18, "max_temp": 30}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<IoTDevice {self.name} ({self.device_type}) in Room {self.room_id}>"


class IoTDeviceLog(BaseModel):
    """IoT cihazı telemetri/olay logu."""
    __tablename__ = "iot_device_logs"

    device_id: Mapped[str] = mapped_column(ForeignKey("iot_devices.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)  # state_change, error, command, reading
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"temperature": 22.5, "humidity": 45}
    source: Mapped[str] = mapped_column(String(20), default="device", nullable=False)  # device, system, user
    performed_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    def __repr__(self) -> str:
        return f"<IoTDeviceLog {self.event_type} for Device {self.device_id}>"


class IoTScenario(BaseModel):
    """Akıllı oda senaryosu/otomasyon kuralı."""
    __tablename__ = "iot_scenarios"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(30), nullable=False)  # time_schedule, sensor, occupancy, manual, checkout
    trigger_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"time": "08:00", "days": ["mon","tue"]}
    actions: Mapped[dict] = mapped_column(JSON, nullable=False)  # [{"device_type": "curtain", "command": "open"}, {"device_type": "light", "command": "set_brightness", "value": 50}]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    applies_to_room_types: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # ["DBL", "SUI"] or null = all

    def __repr__(self) -> str:
        return f"<IoTScenario {self.name} ({self.trigger_type})>"


class IoTEnergyReading(BaseModel):
    """Enerji tüketim okuması (oda bazlı)."""
    __tablename__ = "iot_energy_readings"

    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    device_id: Mapped[Optional[str]] = mapped_column(ForeignKey("iot_devices.id"), nullable=True)
    reading_type: Mapped[str] = mapped_column(String(20), default="electricity", nullable=False)  # electricity, water, gas
    value: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), default="kWh", nullable=False)  # kWh, m3, liter
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<IoTEnergyReading {self.reading_type}: {self.value} {self.unit}>"


class IoTAlert(BaseModel):
    """IoT cihaz uyarı/alert kaydı."""
    __tablename__ = "iot_alerts"

    device_id: Mapped[str] = mapped_column(ForeignKey("iot_devices.id"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)  # temperature_high, device_offline, energy_spike, motion_detected
    severity: Mapped[str] = mapped_column(String(10), default="info", nullable=False)  # info, warning, critical
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    def __repr__(self) -> str:
        return f"<IoTAlert {self.alert_type} ({self.severity})>"
