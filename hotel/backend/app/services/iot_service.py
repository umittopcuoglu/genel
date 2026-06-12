"""
IoT / Smart Room servisi: Cihaz yönetimi, senaryolar, enerji okumaları, alertler.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from app.models.iot import IoTDevice, IoTDeviceLog, IoTScenario, IoTEnergyReading, IoTAlert
from app.schemas.iot import (
    IoTDeviceCreate,
    IoTDeviceUpdate,
    IoTDeviceCommand,
    IoTScenarioCreate,
    IoTScenarioUpdate,
    IoTEnergyReadingCreate,
    IoTAlertResolve,
)


class IoTService:
    """IoT / Smart Room iş mantığı."""

    # ── Device ──

    @staticmethod
    async def create_device(db: AsyncSession, data: IoTDeviceCreate, current_user: dict) -> IoTDevice:
        device = IoTDevice(
            room_id=data.room_id,
            device_type=data.device_type,
            name=data.name,
            vendor=data.vendor,
            model=data.model,
            serial_number=data.serial_number,
            config=data.config,
            ip_address=data.ip_address,
            notes=data.notes,
            created_by=current_user.get("user_id"),
        )
        db.add(device)
        await db.flush()  # device.id (Python-side UUID default) ata → log.device_id için
        # Log cihaz ekleme
        log = IoTDeviceLog(
            device_id=device.id,
            event_type="state_change",
            data={"action": "created"},
            source="system",
            performed_by=current_user.get("user_id"),
            created_by=current_user.get("user_id"),
        )
        db.add(log)
        await db.commit()
        await db.refresh(device)
        return device

    @staticmethod
    async def get_device(db: AsyncSession, device_id: UUID) -> Optional[IoTDevice]:
        stmt = select(IoTDevice).where(IoTDevice.id == device_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_device(db: AsyncSession, device_id: UUID, data: IoTDeviceUpdate, current_user: dict) -> Optional[IoTDevice]:
        device = await IoTService.get_device(db, device_id)
        if not device:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)
        device.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(device)
        return device

    @staticmethod
    async def send_command(db: AsyncSession, device_id: UUID, command: IoTDeviceCommand, current_user: dict) -> Optional[IoTDevice]:
        """Cihaza komut gönder (mock)."""
        device = await IoTService.get_device(db, device_id)
        if not device:
            return None

        # Log komut
        log = IoTDeviceLog(
            device_id=device_id,
            event_type="command",
            data={"command": command.command, "value": command.value},
            source="user",
            performed_by=current_user.get("user_id"),
            created_by=current_user.get("user_id"),
        )
        db.add(log)

        # Simulate state change
        if device.state is None:
            device.state = {}
        if command.value:
            device.state.update(command.value)
        device.last_seen_at = datetime.now()
        device.updated_by = current_user.get("user_id")

        await db.commit()
        await db.refresh(device)
        return device

    @staticmethod
    async def list_devices(
        db: AsyncSession,
        room_id: Optional[UUID] = None,
        device_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[IoTDevice]:
        stmt = select(IoTDevice)
        conditions = []
        if room_id:
            conditions.append(IoTDevice.room_id == room_id)
        if device_type:
            conditions.append(IoTDevice.device_type == device_type)
        if status:
            conditions.append(IoTDevice.status == status)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_device_logs(db: AsyncSession, device_id: UUID, limit: int = 50) -> list[IoTDeviceLog]:
        stmt = select(IoTDeviceLog).where(
            IoTDeviceLog.device_id == device_id
        ).order_by(IoTDeviceLog.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Scenario ──

    @staticmethod
    async def create_scenario(db: AsyncSession, data: IoTScenarioCreate, current_user: dict) -> IoTScenario:
        scenario = IoTScenario(
            name=data.name,
            description=data.description,
            trigger_type=data.trigger_type,
            trigger_config=data.trigger_config,
            actions=data.actions,
            priority=data.priority,
            applies_to_room_types=data.applies_to_room_types,
            created_by=current_user.get("user_id"),
        )
        db.add(scenario)
        await db.commit()
        await db.refresh(scenario)
        return scenario

    @staticmethod
    async def get_scenario(db: AsyncSession, scenario_id: UUID) -> Optional[IoTScenario]:
        stmt = select(IoTScenario).where(IoTScenario.id == scenario_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_scenario(db: AsyncSession, scenario_id: UUID, data: IoTScenarioUpdate, current_user: dict) -> Optional[IoTScenario]:
        scenario = await IoTService.get_scenario(db, scenario_id)
        if not scenario:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(scenario, field, value)
        scenario.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(scenario)
        return scenario

    @staticmethod
    async def list_scenarios(db: AsyncSession, trigger_type: Optional[str] = None, is_active: Optional[bool] = None) -> list[IoTScenario]:
        stmt = select(IoTScenario)
        conditions = []
        if trigger_type:
            conditions.append(IoTScenario.trigger_type == trigger_type)
        if is_active is not None:
            conditions.append(IoTScenario.is_active == is_active)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(IoTScenario.priority.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def trigger_scenario(db: AsyncSession, scenario_id: UUID, current_user: dict) -> Optional[dict]:
        """Senaryoyu manuel tetikle (cihaz komutlarını simüle et)."""
        scenario = await IoTService.get_scenario(db, scenario_id)
        if not scenario:
            return None

        executed_actions = []
        for action in scenario.actions if isinstance(scenario.actions, list) else [scenario.actions]:
            executed_actions.append({
                "action": action,
                "status": "simulated",
                "message": f"Komut simüle edildi: {action.get('command', 'unknown')}",
            })

        return {
            "scenario_id": str(scenario_id),
            "scenario_name": scenario.name,
            "actions_executed": len(executed_actions),
            "details": executed_actions,
        }

    # ── Energy Reading ──

    @staticmethod
    async def record_energy(db: AsyncSession, data: IoTEnergyReadingCreate, current_user: dict) -> IoTEnergyReading:
        reading = IoTEnergyReading(
            room_id=data.room_id,
            device_id=data.device_id,
            reading_type=data.reading_type,
            value=data.value,
            unit=data.unit,
            recorded_at=data.recorded_at or datetime.now(),
            created_by=current_user.get("user_id"),
        )
        db.add(reading)
        await db.commit()
        await db.refresh(reading)
        return reading

    @staticmethod
    async def list_energy_readings(
        db: AsyncSession,
        room_id: Optional[UUID] = None,
        reading_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[IoTEnergyReading]:
        stmt = select(IoTEnergyReading)
        conditions = []
        if room_id:
            conditions.append(IoTEnergyReading.room_id == room_id)
        if reading_type:
            conditions.append(IoTEnergyReading.reading_type == reading_type)
        if date_from:
            conditions.append(IoTEnergyReading.recorded_at >= date_from)
        if date_to:
            conditions.append(IoTEnergyReading.recorded_at <= date_to)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(IoTEnergyReading.recorded_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Alert ──

    @staticmethod
    async def resolve_alert(db: AsyncSession, alert_id: UUID, data: IoTAlertResolve, current_user: dict) -> Optional[IoTAlert]:
        stmt = select(IoTAlert).where(IoTAlert.id == alert_id)
        result = await db.execute(stmt)
        alert = result.scalar_one_or_none()
        if not alert:
            return None
        alert.is_resolved = data.is_resolved
        alert.resolved_at = datetime.now()
        alert.resolved_by = current_user.get("user_id")
        alert.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(alert)
        return alert

    @staticmethod
    async def list_alerts(
        db: AsyncSession,
        device_id: Optional[UUID] = None,
        severity: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        limit: int = 50,
    ) -> list[IoTAlert]:
        stmt = select(IoTAlert)
        conditions = []
        if device_id:
            conditions.append(IoTAlert.device_id == device_id)
        if severity:
            conditions.append(IoTAlert.severity == severity)
        if is_resolved is not None:
            conditions.append(IoTAlert.is_resolved == is_resolved)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(IoTAlert.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
