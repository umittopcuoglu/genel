"""
Computer Vision entegrasyon base adapter.
"""
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel


class CVInferenceResult(BaseModel):
    """CV model inference sonucu."""
    defects: list[dict]
    objects: list[dict]
    confidence: float
    inference_time_ms: int


class CVAdapter(ABC):
    """CV entegrasyonu için base adapter."""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def analyze_image(self, image_path: str, model_name: str) -> CVInferenceResult:
        """Görüntüyü analiz et, kusur ve objeleri tespit et."""
        pass

    @abstractmethod
    async def detect_objects(self, image_path: str, model_name: str) -> list[dict]:
        """Nesne tespiti yap."""
        pass

    @abstractmethod
    async def count_items(self, image_path: str, item_type: str) -> int:
        """Belirli bir eşyayı say."""
        pass
