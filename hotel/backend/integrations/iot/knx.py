"""
KNX IoT adapter mock - Bina otomasyonu (perde, ışık, enerji).
"""
import logging
from typing import Optional
from datetime import datetime

from integrations.iot.base import IoTAdapter, IoTDeviceInfo, IoTCommand, IoTCommandResult

logger = logging.getLogger(__name__)


class KNXAdapter(IoTAdapter):
    """KNX bina otomasyonu entegrasyonu (mock)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.gateway_ip = config.get("gateway_ip", "192.168.1.100")
        logger.info(f"KNXAdapter initialized with gateway: {self.gateway_ip}")

    async def get_device(self, device_id: str) -> Optional[IoTDeviceInfo]:
        logger.info(f"[KNX] Getting device: {device_id}")
        return IoTDeviceInfo(
            device_id=device_id,
            device_type="curtain",
            name=f"KNX Curtain {device_id[-4:]}",
            vendor="knx",
            model="KNX Standard Actuator",
            status="online",
            state={"position": 50, "is_moving": False},
            last_seen=datetime.now().isoformat(),
        )

    async def send_command(self, device_id: str, command: IoTCommand) -> IoTCommandResult:
        logger.info(f"[KNX] Sending command '{command.command}' to {device_id}")
        return IoTCommandResult(
            success=True,
            device_id=device_id,
            new_state={"position": command.params.get("position", 100)} if command.params else None,
            message=f"KNX komut uygulandı: {command.command}",
        )

    async def get_devices_by_room(self, room_id: str) -> list[IoTDeviceInfo]:
        logger.info(f"[KNX] Getting devices for room: {room_id}")
        return [
            IoTDeviceInfo(
                device_id=f"knx-curtain-{room_id}",
                device_type="curtain",
                name="KNX Perde",
                vendor="knx",
                model="KNX Curtain Actuator",
                status="online",
                state={"position": 0},
                last_seen=datetime.now().isoformat(),
            ),
            IoTDeviceInfo(
                device_id=f"knx-light-{room_id}",
                device_type="light",
                name="KNX Ana Aydınlatma",
                vendor="knx",
                model="KNX Dimmer",
                status="online",
                state={"brightness": 100, "is_on": True},
                last_seen=datetime.now().isoformat(),
            ),
        ]

    async def set_scene(self, room_id: str, scene_name: str) -> bool:
        logger.info(f"[KNX] Setting scene '{scene_name}' for room {room_id}")
        scenes = {
            "good_morning": "Perdeler açıldı, ışıklar %30",
            "good_night": "Perdeler kapandı, ışıklar kapandı",
            "energy_save": "Perdeler kapandı, ışıklar kapandı, sıcaklık 18°C",
            "cleaning": "Perdeler açıldı, ışıklar %100",
        }
        logger.info(f"[KNX] Scene '{scene_name}': {scenes.get(scene_name, 'Bilinmeyen senaryo')}")
        return True
