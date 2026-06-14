"""
TASK-015 — TechCare AI: Arıza triyajı (kategori+öncelik+tahmini süre) + arıza riski.
Mock-first: anahtar kelime tabanlı deterministik sınıflandırma.
"""
from pydantic import BaseModel
from app.core.agents.base import BaseAgent


class TechCareInput(BaseModel):
    description: str


class TechCareOutput(BaseModel):
    category: str
    priority: str
    estimated_hours: int
    confidence: float
    rationale: str


# Anahtar kelime → (kategori, öncelik, tahmini saat)
_KEYWORDS = [
    (["yangın", "fire", "duman", "gaz", "gas", "leak", "kaçak"], "Safety", "urgent", 1),
    (["su", "water", "tıka", "sızıntı", "plumb", "musluk", "lavabo"], "Plumbing", "high", 2),
    (["elektrik", "electric", "priz", "kısa devre", "power", "ışık", "light"], "Electrical", "high", 2),
    (["klima", "ac", "hvac", "ısıtma", "soğutma", "heating", "cooling"], "HVAC", "normal", 3),
    (["kapı", "door", "kilit", "lock", "pencere", "window"], "Carpentry", "normal", 2),
]


class TechCareAgent(BaseAgent):
    agent_name = "tech_care"
    model_provider = "deepseek"
    prompt_version = "1.0.0"

    async def _run(
        self, input_schema: TechCareInput, context=None, db=None, user=None
    ) -> TechCareOutput:
        text = input_schema.description.lower()
        for keywords, category, priority, hours in _KEYWORDS:
            if any(k in text for k in keywords):
                return TechCareOutput(
                    category=category,
                    priority=priority,
                    estimated_hours=hours,
                    confidence=0.82,
                    rationale=f"Açıklama '{category}' kategorisine eşleşti; öncelik={priority}.",
                )
        return TechCareOutput(
            category="General",
            priority="normal",
            estimated_hours=2,
            confidence=0.55,
            rationale="Belirgin anahtar kelime yok; genel bakım olarak sınıflandırıldı.",
        )
