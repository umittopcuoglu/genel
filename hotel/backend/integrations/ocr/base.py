"""
OCR belge tarama base adapter.
"""
from abc import ABC, abstractmethod
from typing import Optional, Any
from pydantic import BaseModel


class OCRResult(BaseModel):
    """OCR tarama sonucu."""
    raw_text: str
    mrz_text: Optional[str] = None
    confidence: float
    fields: dict[str, Any]


class OCRAdapter(ABC):
    """OCR entegrasyonu için base adapter."""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def scan_document(self, image_path: str) -> OCRResult:
        """Belgeyi tara ve OCR sonucunu döndür."""
        pass

    @abstractmethod
    async def scan_passport(self, image_path: str) -> OCRResult:
        """Pasaport MRZ tara."""
        pass

    @abstractmethod
    async def scan_national_id(self, image_path: str) -> OCRResult:
        """Kimlik kartı tara."""
        pass
