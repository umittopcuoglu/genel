"""
EGM (Emniyet Genel Müdürlüğü) bildirim servisi (mock).
"""
import logging
from typing import Optional
from random import randint, choice
from datetime import datetime

logger = logging.getLogger(__name__)


class EGMService:
    """
    EGM misafir bildirim servisi (mock).
    Gerçek implementasyonda EGM web servisine SOAP XML gönderir.
    """

    def __init__(self, config: dict):
        self.endpoint = config.get("endpoint", "https://egm.gov.tr/kayit")
        self.tesis_kodu = config.get("tesis_kodu", "MOCK001")
        self.api_key = config.get("api_key", "mock_egm_key")
        logger.info(f"EGMService initialized: {self.tesis_kodu} @ {self.endpoint}")

    async def submit_checkin(self, guest_data: dict, stay_data: dict) -> dict:
        """Giriş bildirimi gönder (mock)."""
        logger.info(f"[EGM] Submitting check-in for {guest_data.get('first_name', '')} {guest_data.get('last_name', '')}")
        return {
            "success": True,
            "response_code": "00",
            "response_message": "İşlem başarılı",
            "reference_number": f"EGM-{randint(100000, 999999)}",
            "submitted_at": datetime.now().isoformat(),
        }

    async def submit_checkout(self, stay_id: str) -> dict:
        """Çıkış bildirimi gönder (mock)."""
        logger.info(f"[EGM] Submitting checkout for stay {stay_id}")
        return {
            "success": True,
            "response_code": "00",
            "response_message": "Çıkış bildirimi başarılı",
            "reference_number": f"EGM-{randint(100000, 999999)}",
            "submitted_at": datetime.now().isoformat(),
        }

    async def generate_xml(self, guest_data: dict, stay_data: dict) -> str:
        """EGM XML payload oluştur (mock)."""
        import xml.etree.ElementTree as ET

        root = ET.Element("EGM_Bildirim")
        islem = ET.SubElement(root, "IslemTuru")
        islem.text = "GIRIS"
        tesis = ET.SubElement(root, "TesisKodu")
        tesis.text = self.tesis_kodu
        musteri = ET.SubElement(root, "Musteri")
        ad = ET.SubElement(musteri, "Ad")
        ad.text = guest_data.get("first_name", "")
        soyad = ET.SubElement(musteri, "Soyad")
        soyad.text = guest_data.get("last_name", "")
        kimlik = ET.SubElement(musteri, "KimlikNo")
        kimlik.text = guest_data.get("document_number", "")

        return ET.tostring(root, encoding="unicode")

    async def health_check(self) -> dict:
        """EGM servis durumu (mock)."""
        return {
            "service": "EGM",
            "status": "healthy",
            "endpoint": self.endpoint,
            "response_time_ms": randint(50, 300),
        }
