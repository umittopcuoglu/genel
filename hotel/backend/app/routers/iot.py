"""
IoT / Smart Room router: Device, Scenario, Energy, Alert endpoint'leri.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from typing import List

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.user import User
from app.schemas.iot import (
    IoTDeviceCreate,
    IoTDeviceResponse,
    IoTDeviceUpdate,
    IoTDeviceCommand,
    IoTDeviceLogResponse,
    IoTScenarioCreate,
    IoTScenarioResponse,
    IoTScenarioUpdate,
    IoTEnergyReadingCreate,
    IoTEnergyReadingResponse,
    IoTAlertResponse,
    IoTAlertResolve,
)
from app.services.iot_service import IoTService

router = APIRouter(prefix="/api/v1/iot", tags=["IoT / Smart Rooms"])


# ── Device Endpoints ──

@router.post("/devices", response_model=IoTDeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    data: IoTDeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Yeni IoT cihazı oluştur."""
    return await IoTService.create_device(db, data, {"user_id": str(current_user.id)})


@router.get("/devices", response_model=List[IoTDeviceResponse])
async def list_devices(
    room_id: UUID = Query(None),
    device_type: str = Query(None, description="thermostat, light, curtain, tv, sensor, lock, speaker"),
    status: str = Query(None, description="online, offline, error, maintenance"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance", "frontdesk"])),
):
    """IoT cihazlarını listele."""
    return await IoTService.list_devices(db, room_id=room_id, device_type=device_type, status=status)


@router.get("/devices/{device_id}", response_model=IoTDeviceResponse)
async def get_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance", "frontdesk"])),
):
    """Cihaz detayını getir."""
    device = await IoTService.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cihaz bulunamadı")
    return device


@router.patch("/devices/{device_id}", response_model=IoTDeviceResponse)
async def update_device(
    device_id: UUID,
    data: IoTDeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Cihaz bilgilerini güncelle."""
    device = await IoTService.update_device(db, device_id, data, {"user_id": str(current_user.id)})
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cihaz bulunamadı")
    return device


@router.post("/devices/{device_id}/command", response_model=IoTDeviceResponse)
async def send_command(
    device_id: UUID,
    command: IoTDeviceCommand,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance", "frontdesk"])),
):
    """Cihaza komut gönder (aç/kapa, sıcaklık ayarla, perde aç/kapa vb.)."""
    device = await IoTService.send_command(db, device_id, command, {"user_id": str(current_user.id)})
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cihaz bulunamadı")
    return device


@router.get("/devices/{device_id}/logs", response_model=List[IoTDeviceLogResponse])
async def get_device_logs(
    device_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Cihaz loglarını getir."""
    return await IoTService.get_device_logs(db, device_id, limit=limit)


# ── Scenario Endpoints ──

@router.post("/scenarios", response_model=IoTScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    data: IoTScenarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Yeni otomasyon senaryosu oluştur."""
    return await IoTService.create_scenario(db, data, {"user_id": str(current_user.id)})


@router.get("/scenarios", response_model=List[IoTScenarioResponse])
async def list_scenarios(
    trigger_type: str = Query(None, description="time_schedule, sensor, occupancy, manual, checkout"),
    is_active: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Senaryoları listele."""
    return await IoTService.list_scenarios(db, trigger_type=trigger_type, is_active=is_active)


@router.get("/scenarios/{scenario_id}", response_model=IoTScenarioResponse)
async def get_scenario(
    scenario_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Senaryo detayını getir."""
    scenario = await IoTService.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Senaryo bulunamadı")
    return scenario


@router.patch("/scenarios/{scenario_id}", response_model=IoTScenarioResponse)
async def update_scenario(
    scenario_id: UUID,
    data: IoTScenarioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Senaryoyu güncelle."""
    scenario = await IoTService.update_scenario(db, scenario_id, data, {"user_id": str(current_user.id)})
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Senaryo bulunamadı")
    return scenario


@router.post("/scenarios/{scenario_id}/trigger")
async def trigger_scenario(
    scenario_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Senaryoyu manuel tetikle."""
    result = await IoTService.trigger_scenario(db, scenario_id, {"user_id": str(current_user.id)})
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Senaryo bulunamadı")
    return result


# ── Energy Endpoints ──

@router.post("/energy", response_model=IoTEnergyReadingResponse, status_code=status.HTTP_201_CREATED)
async def record_energy(
    data: IoTEnergyReadingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Enerji tüketim okuması kaydet."""
    return await IoTService.record_energy(db, data, {"user_id": str(current_user.id)})


@router.get("/energy", response_model=List[IoTEnergyReadingResponse])
async def list_energy_readings(
    room_id: UUID = Query(None),
    reading_type: str = Query(None, description="electricity, water, gas"),
    date_from: datetime = Query(None),
    date_to: datetime = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Enerji tüketim kayıtlarını listele."""
    return await IoTService.list_energy_readings(
        db, room_id=room_id, reading_type=reading_type, date_from=date_from, date_to=date_to, limit=limit
    )


# ── Alert Endpoints ──

@router.get("/alerts", response_model=List[IoTAlertResponse])
async def list_alerts(
    device_id: UUID = Query(None),
    severity: str = Query(None, description="info, warning, critical"),
    is_resolved: bool = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """IoT uyarılarını listele."""
    return await IoTService.list_alerts(
        db, device_id=device_id, severity=severity, is_resolved=is_resolved, limit=limit
    )


@router.post("/alerts/{alert_id}/resolve", response_model=IoTAlertResponse)
async def resolve_alert(
    alert_id: UUID,
    data: IoTAlertResolve,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Uyarıyı çözüldü olarak işaretle."""
    alert = await IoTService.resolve_alert(db, alert_id, data, {"user_id": str(current_user.id)})
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uyarı bulunamadı")
    return alert
