"""
Tesseract OCR servisi (mock) — MRZ + alan çıkarımı simüle eder.
"""
import logging
from typing import Optional
from random import uniform, randint, choice

from integrations.ocr.base import OCRAdapter, OCRResult

logger = logging.getLogger(__name__)


class TesseractService(OCRAdapter):
    """Tesseract OCR mock servisi."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.language = config.get("language", "tur+eng")
        self.tesseract_path = config.get("tesseract_path", "C:/Program Files/Tesseract-OCR/tesseract.exe")
        logger.info(f"TesseractService initialized: {self.language}")

    async def scan_document(self, image_path: str) -> OCRResult:
        logger.info(f"[OCR] Scanning document: {image_path}")
        first_names = ["JOHN", "JANE", "AHMET", "AYSE", "MICHAEL", "MARIA"]
        last_names = ["DOE", "SMITH", "YILMAZ", "KAYA", "BROWN"]
        fn = choice(first_names)
        ln = choice(last_names)

        return OCRResult(
            raw_text=f"P<UTOMOCK{fn}<<{ln}<<<<<<<<<<<<<<<<<<<<\n{randint(1000000, 9999999)}",
            mrz_text=f"P<UTO{fn[0]}<<{ln[0]}<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
            confidence=round(uniform(85, 99), 2),
            fields={
                "document_type": "P",
                "issuing_country": "UTO",
                "document_number": f"U{randint(1000000, 9999999)}",
                "first_name": fn,
                "last_name": ln,
                "nationality": "TR",
                "date_of_birth": f"{randint(1, 28):02d}{randint(1, 12):02d}{randint(1970, 2000)}",
                "gender": choice(["M", "F"]),
                "expiry_date": f"{randint(1, 28):02d}{randint(1, 12):02d}{randint(2028, 2035)}",
            },
        )

    async def scan_passport(self, image_path: str) -> OCRResult:
        logger.info(f"[OCR] Scanning passport: {image_path}")
        return await self.scan_document(image_path)

    async def scan_national_id(self, image_path: str) -> OCRResult:
        logger.info(f"[OCR] Scanning national ID: {image_path}")
        return OCRResult(
            raw_text=f"TC KİMLİK NO: {randint(10000000000, 99999999999)}",
            mrz_text=None,
            confidence=round(uniform(80, 98), 2),
            fields={
                "document_type": "ID",
                "document_number": str(randint(10000000000, 99999999999)),
                "first_name": choice(["ALI", "AYSE", "MEHMET", "ZEYNEP"]),
                "last_name": choice(["YILMAZ", "KAYA", "DEMIR", "CELIK"]),
                "date_of_birth": f"{randint(1, 28):02d}.{randint(1, 12):02d}.{randint(1970, 2000)}",
            },
        )
