import re
from typing import Tuple


class PIIMasker:
    MASK_PATTERNS = {
        "ad": r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)*\b",
        "telefon": r"\b(?:\+90|0)[0-9]{10}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "tc": r"\b[0-9]{11}\b",
    }

    @staticmethod
    def mask(text: str, context: dict | None = None) -> Tuple[str, dict]:
        masked_text = text
        mask_map = {}
        counter = {}

        for pii_type, pattern in PIIMasker.MASK_PATTERNS.items():
            matches = re.findall(pattern, text)
            counter[pii_type] = 0
            for match in matches:
                placeholder = f"[MASKED_{pii_type.upper()}_{counter[pii_type]}]"
                masked_text = masked_text.replace(match, placeholder, 1)
                mask_map[placeholder] = match
                counter[pii_type] += 1

        return masked_text, mask_map

    @staticmethod
    def unmask(llm_response: str, mask_map: dict) -> str:
        result = llm_response
        for placeholder, original in mask_map.items():
            result = result.replace(placeholder, original)
        return result
