"""
IoT / Smart Room entegrasyon base adapter.
Tüm IoT sağlayıcıları (Nest, KNX, Philips Hue) bu adapter'ı temel alır.
"""
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel


class IoTDeviceInfo(BaseModel):
    """IoT cihaz bilgisi."""
    device_id: str
    device_type: str
    name: str
    vendor: str
    model: str
    status: str  # online, offline
    state: Optional[dict] = None
    last_seen: Optional[str] = None


class IoTCommand(BaseModel):
    """IoT cihazına gönderilecek komut."""
    command: str
    params: Optional[dict] = None


class IoTCommandResult(BaseModel):
    """Komut sonucu."""
    success: bool
    device_id: str
    new_state: Optional[dict] = None
    message: Optional[str] = None


class IoTAdapter(ABC):
    """
    IoT cihaz entegrasyonu için base adapter.
    Her IoT sağlayıcısı (Nest, KNX, Hue) bu sınıfı implemente eder.
    """

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def get_device(self, device_id: str) -> Optional[IoTDeviceInfo]:
        """Cihaz bilgisini getir."""
        pass

    @abstractmethod
    async def send_command(self, device_id: str, command: IoTCommand) -> IoTCommandResult:
        """Cihaza komut gönder."""
        pass

    @abstractmethod
    async def get_devices_by_room(self, room_id: str) -> list[IoTDeviceInfo]:
        """Odaya ait tüm cihazları getir."""
        pass

    @abstractmethod
    async def set_scene(self, room_id: str, scene_name: str) -> bool:
        """Odaya senaryo uygula (örn: 'good_morning', 'good_night', 'energy_save')."""
        pass
