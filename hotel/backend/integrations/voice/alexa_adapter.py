"""
Alexa skill adapter (mock).
"""
import logging
from typing import Optional

from integrations.voice.base import VoiceAdapter

logger = logging.getLogger(__name__)


class AlexaAdapter(VoiceAdapter):
    """Alexa skill entegrasyonu (mock)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.skill_id = config.get("skill_id", "amzn1.ask.skill.mock")
        logger.info(f"AlexaAdapter initialized with skill: {self.skill_id}")

    async def process_intent(self, intent: str, slots: dict, session_id: str) -> dict:
        logger.info(f"[Alexa] Processing intent: {intent}")
        responses = {
            "SetTemperature": f"Sıcaklık {slots.get('temperature', '22')} dereceye ayarlandı.",
            "TurnOnLight": "Işıklar açıldı.",
            "TurnOffLight": "Işıklar kapatıldı.",
            "CallHousekeeping": "Kat hizmetlerine haber verildi.",
            "OrderRoomService": "Oda servisi siparişiniz alındı.",
            "AMAZON.HelpIntent": "Şu komutları kullanabilirsiniz: sıcaklık ayarla, ışıkları aç/kapat, kat hizmetleri çağır.",
            "AMAZON.CancelIntent": "İşlem iptal edildi.",
            "AMAZON.StopIntent": "Görüşmek üzere!",
        }
        speech = responses.get(intent, f"'{intent}' komutu için yanıt bulunamadı.")
        return {
            "version": "1.0",
            "response": {
                "outputSpeech": {"type": "PlainText", "text": speech},
                "shouldEndSession": intent in ("AMAZON.StopIntent", "AMAZON.CancelIntent"),
            },
        }

    async def launch_request(self, session_id: str) -> dict:
        return {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "HotelOps sesli asistana hoş geldiniz. Size nasıl yardımcı olabilirim?",
                },
                "shouldEndSession": False,
            },
        }

    async def session_ended(self, session_id: str) -> dict:
        logger.info(f"[Alexa] Session ended: {session_id}")
        return {"version": "1.0", "response": {}}
