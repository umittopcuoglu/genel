"""
Google Assistant adapter (mock).
"""
import logging
from typing import Optional

from integrations.voice.base import VoiceAdapter

logger = logging.getLogger(__name__)


class GoogleAdapter(VoiceAdapter):
    """Google Actions entegrasyonu (mock)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.project_id = config.get("project_id", "hotelops-mock")
        logger.info(f"GoogleAdapter initialized with project: {self.project_id}")

    async def process_intent(self, intent: str, slots: dict, session_id: str) -> dict:
        logger.info(f"[Google] Processing intent: {intent}")
        responses = {
            "set_temperature": f"Sıcaklık {slots.get('temperature', '22')} dereceye ayarlandı.",
            "turn_on_light": "Işıklar açıldı.",
            "turn_off_light": "Işıklar kapatıldı.",
            "call_housekeeping": "Kat hizmetlerine haber verildi.",
            "order_room_service": "Oda servisi siparişiniz alındı.",
            "goodbye": "Görüşmek üzere!",
        }
        speech = responses.get(intent, f"'{intent}' komutu tanınmadı.")
        return {
            "payload": {
                "google": {
                    "expectUserResponse": True,
                    "richResponse": {
                        "items": [{"simpleResponse": {"textToSpeech": speech}}],
                    },
                }
            }
        }

    async def launch_request(self, session_id: str) -> dict:
        return {
            "payload": {
                "google": {
                    "expectUserResponse": True,
                    "richResponse": {
                        "items": [{
                            "simpleResponse": {
                                "textToSpeech": "HotelOps sesli asistana hoş geldiniz. Size nasıl yardımcı olabilirim?"
                            }
                        }],
                    },
                }
            }
        }

    async def session_ended(self, session_id: str) -> dict:
        logger.info(f"[Google] Session ended: {session_id}")
        return {"payload": {"google": {"expectUserResponse": False}}}
