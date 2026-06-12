"""
YOLOv8 CV servisi (mock) — random defect + confidence üretir.
"""
import logging
from random import uniform, randint, choice
from typing import Optional

from integrations.cv.base import CVAdapter, CVInferenceResult

logger = logging.getLogger(__name__)


class YOLOv8Service(CVAdapter):
    """YOLOv8 mock CV servisi."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.model_path = config.get("model_path", "models/yolov8_room_inspection.pt")
        self.confidence_threshold = config.get("confidence_threshold", 0.5)
        logger.info(f"YOLOv8Service initialized with model: {self.model_path}")

    async def analyze_image(self, image_path: str, model_name: str = "yolov8_room") -> CVInferenceResult:
        """Görüntüyü analiz et (mock)."""
        logger.info(f"Analyzing image: {image_path} with model {model_name}")

        defect_types = ["dirty_carpet", "broken_lamp", "stained_bedding", "leaky_faucet", "missing_towel"]
        num_defects = randint(0, 4)

        defects = []
        for _ in range(num_defects):
            dt = choice(defect_types)
            defects.append({
                "defect_type": dt,
                "confidence": round(uniform(0.65, 0.99), 2),
                "bbox": {"x": randint(0, 800), "y": randint(0, 600), "w": randint(30, 300), "h": randint(30, 300)},
            })

        return CVInferenceResult(
            defects=defects,
            objects=[{"label": "towel", "count": randint(2, 6)}, {"label": "pillow", "count": randint(1, 4)}],
            confidence=round(uniform(0.75, 0.98), 2),
            inference_time_ms=randint(150, 2000),
        )

    async def detect_objects(self, image_path: str, model_name: str = "yolov8_room") -> list[dict]:
        """Nesne tespiti (mock)."""
        items = ["towel", "pillow", "blanket", "hanger", "glass", "remote", "lamp", "chair"]
        results = []
        for item in choice(items):
            results.append({
                "label": item,
                "count": randint(0, 6),
                "confidence": round(uniform(0.7, 0.99), 2),
            })
        return results

    async def count_items(self, image_path: str, item_type: str) -> int:
        """Belirli bir eşyayı say (mock)."""
        base_count = {"towel": 4, "pillow": 4, "blanket": 2, "hanger": 6, "glass": 2, "remote": 1}
        return base_count.get(item_type, randint(0, 6))
