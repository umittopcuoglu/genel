"""
DeepFace yüz tanıma servisi (mock).
"""
import logging
from typing import Optional
from random import uniform, randint

logger = logging.getLogger(__name__)


class DeepFaceService:
    """DeepFace yüz tanıma mock servisi."""

    def __init__(self, config: dict):
        self.model = config.get("model", "Facenet512")
        self.detector = config.get("detector", "opencv")
        logger.info(f"DeepFaceService initialized: {self.model}/{self.detector}")

    async def verify(self, img1_path: str, img2_path: str) -> dict:
        """İki yüzü karşılaştır (mock)."""
        logger.info(f"[Face] Verifying {img1_path} vs {img2_path}")
        similarity = round(uniform(0.65, 0.99), 2)
        return {
            "verified": similarity >= 0.75,
            "similarity": similarity,
            "distance": round(1 - similarity, 4),
            "model": self.model,
            "detector": self.detector,
            "time_ms": randint(100, 800),
        }

    async def detect_face(self, image_path: str) -> dict:
        """Yüz tespiti (mock)."""
        logger.info(f"[Face] Detecting face in: {image_path}")
        return {
            "face_detected": True,
            "confidence": round(uniform(0.92, 0.99), 2),
            "bounding_box": {"x": randint(100, 300), "y": randint(100, 300), "w": 200, "h": 250},
            "landmarks": {"left_eye": [250, 200], "right_eye": [350, 200], "nose": [300, 260]},
        }

    async def liveness_check(self, image_path: str) -> dict:
        """Canlılık kontrolü (mock)."""
        logger.info(f"[Face] Liveness check: {image_path}")
        return {
            "is_live": True,
            "liveness_score": round(uniform(0.85, 0.99), 2),
            "method": "blink_detection",
        }
