"""
Sesli asistan entegrasyon base adapter.
"""
from abc import ABC, abstractmethod
from typing import Optional


class VoiceAdapter(ABC):
    """Sesli asistan entegrasyonu için base adapter."""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def process_intent(self, intent: str, slots: dict, session_id: str) -> dict:
        """Intent'i işle ve yanıt döndür."""
        pass

    @abstractmethod
    async def launch_request(self, session_id: str) -> dict:
        """Skill/action başlatıldığında karşılama mesajı."""
        pass

    @abstractmethod
    async def session_ended(self, session_id: str) -> dict:
        """Oturum sonlandı."""
        pass
