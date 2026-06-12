"""
Philips Hue IoT adapter mock - Akıllı aydınlatma.
"""
import logging
from typing import Optional
from datetime import datetime

from integrations.iot.base import IoTAdapter, IoTDeviceInfo, IoTCommand, IoTCommandResult

logger = logging.getLogger(__name__)


class HueAdapter(IoTAdapter):
    """Philips Hue aydınlatma entegrasyonu (mock)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.bridge_ip = config.get("bridge_ip", "192.168.1.101")
        self.api_key = config.get("api_key", "mock_hue_key")
        logger.info(f"HueAdapter initialized with bridge: {self.bridge_ip}")

    async def get_device(self, device_id: str) -> Optional[IoTDeviceInfo]:
        logger.info(f"[Hue] Getting device: {device_id}")
        return IoTDeviceInfo(
            device_id=device_id,
            device_type="light",
            name=f"Hue Light {device_id[-4:]}",
            vendor="philips",
            model="Hue White & Color Ambiance",
            status="online",
            state={"is_on": True, "brightness": 80, "hue": 0, "saturation": 0, "color": "warm_white"},
            last_seen=datetime.now().isoformat(),
        )

    async def send_command(self, device_id: str, command: IoTCommand) -> IoTCommandResult:
        logger.info(f"[Hue] Sending command '{command.command}' to {device_id}")
        new_state = {}
        if command.params:
            if "brightness" in command.params:
                new_state["brightness"] = command.params["brightness"]
            if "color" in command.params:
                new_state["color"] = command.params["color"]
            if "is_on" in command.params:
                new_state["is_on"] = command.params["is_on"]

        return IoTCommandResult(
            success=True,
            device_id=device_id,
            new_state=new_state,
            message=f"Hue ışık komutu uygulandı: {command.command}",
        )

    async def get_devices_by_room(self, room_id: str) -> list[IoTDeviceInfo]:
        logger.info(f"[Hue] Getting devices for room: {room_id}")
        return [
            IoTDeviceInfo(
                device_id=f"hue-ceiling-{room_id}",
                device_type="light",
                name="Tavan Aydınlatması",
                vendor="philips",
                model="Hue White Ambiance",
                status="online",
                state={"is_on": True, "brightness": 70},
                last_seen=datetime.now().isoformat(),
            ),
            IoTDeviceInfo(
                device_id=f"hue-nightstand-{room_id}",
                device_type="light",
                name="Komidin Lambası",
                vendor="philips",
                model="Hue White",
                status="online",
                state={"is_on": False, "brightness": 0},
                last_seen=datetime.now().isoformat(),
            ),
        ]

    async def set_scene(self, room_id: str, scene_name: str) -> bool:
        logger.info(f"[Hue] Setting scene '{scene_name}' for room {room_id}")
        scenes = {
            "good_morning": "Aydınlatma %50, gün ışığı modu",
            "good_night": "Tüm ışıklar kapalı, gece lambası %10",
            "romantic": "Loş ışık %20, sıcak renk",
            "reading": "Komidin lambası %80, tavan loş",
        }
        logger.info(f"[Hue] Scene '{scene_name}': {scenes.get(scene_name, 'Bilinmeyen senaryo')}")
        return True
