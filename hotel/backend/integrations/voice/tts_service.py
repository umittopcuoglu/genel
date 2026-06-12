"""
Text-to-Speech servisi (mock) — base64 ses çıktısı üretir.
"""
import logging
import base64
from typing import Optional

logger = logging.getLogger(__name__)


class TTSService:
    """Mock TTS servisi — gerçek bir API çağrısı yapmaz, dummy base64 döndürür."""

    def __init__(self, config: dict):
        self.language = config.get("language", "tr-TR")
        self.voice = config.get("voice", "tr-TR-Wavenet-A")
        logger.info(f"TTSService initialized: {self.language}/{self.voice}")

    async def synthesize(self, text: str, language: Optional[str] = None) -> str:
        """Metni sese çevir (mock — dummy base64)."""
        logger.info(f"[TTS] Synthesizing: '{text[:50]}...'")
        # Gerçekte Google Cloud TTS / Amazon Polly çağrısı yapılır
        # Mock: dummy base64 audio data
        dummy_audio = b"MOCK_AUDIO_DATA_FOR_" + text.encode("utf-8")
        return base64.b64encode(dummy_audio).decode("utf-8")

    async def get_voices(self) -> list[dict]:
        """Mevcut sesleri listele (mock)."""
        return [
            {"name": "tr-TR-Wavenet-A", "language": "tr-TR", "gender": "FEMALE"},
            {"name": "tr-TR-Wavenet-B", "language": "tr-TR", "gender": "MALE"},
            {"name": "en-US-Wavenet-C", "language": "en-US", "gender": "FEMALE"},
            {"name": "en-US-Wavenet-D", "language": "en-US", "gender": "MALE"},
        ]
