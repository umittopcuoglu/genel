"""
Nest (Google) IoT adapter mock - Termostat, sıcaklık kontrolü.
"""
import logging
from typing import Optional
from datetime import datetime

from integrations.iot.base import IoTAdapter, IoTDeviceInfo, IoTCommand, IoTCommandResult

logger = logging.getLogger(__name__)


class NestAdapter(IoTAdapter):
    """Nest termostat entegrasyonu (mock)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key", "mock_nest_key")
        self.project_id = config.get("project_id", "mock-project")
        logger.info("NestAdapter initialized")

    async def get_device(self, device_id: str) -> Optional[IoTDeviceInfo]:
        logger.info(f"[Nest] Getting device: {device_id}")
        return IoTDeviceInfo(
            device_id=device_id,
            device_type="thermostat",
            name="Nest Thermostat",
            vendor="google",
            model="Nest Learning Thermostat 3rd Gen",
            status="online",
            state={"temperature": 22.5, "humidity": 45, "mode": "cool", "fan": "auto"},
            last_seen=datetime.now().isoformat(),
        )

    async def send_command(self, device_id: str, command: IoTCommand) -> IoTCommandResult:
        logger.info(f"[Nest] Sending command '{command.command}' to {device_id}")
        return IoTCommandResult(
            success=True,
            device_id=device_id,
            new_state={"temperature": command.params.get("temperature", 22.0)} if command.params else None,
            message=f"Komut '{command.command}' başarıyla uygulandı",
        )

    async def get_devices_by_room(self, room_id: str) -> list[IoTDeviceInfo]:
        logger.info(f"[Nest] Getting devices for room: {room_id}")
        return [
            IoTDeviceInfo(
                device_id=f"nest-thermo-{room_id}",
                device_type="thermostat",
                name="Nest Thermostat",
                vendor="google",
                model="Nest Learning Thermostat",
                status="online",
                state={"temperature": 22.0, "humidity": 48},
                last_seen=datetime.now().isoformat(),
            )
        ]

    async def set_scene(self, room_id: str, scene_name: str) -> bool:
        logger.info(f"[Nest] Setting scene '{scene_name}' for room {room_id}")
        return True
