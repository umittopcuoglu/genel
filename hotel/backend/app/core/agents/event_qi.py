"""
TASK-014 — EventIQ AI: Etkinlik kurulumu önerisi + grup upsell fırsatları.
Mock-first: LLM anahtarı yoksa deterministik öneri üretir.
"""
from typing import Optional
from pydantic import BaseModel
from app.core.agents.base import BaseAgent


class EventIQInput(BaseModel):
    event_type: str = "conference"
    pax_count: int = 100
    group_preferences: Optional[str] = None


class EventIQOutput(BaseModel):
    venue_suggestion: str
    setup_type: str
    capacity: int
    catering_items: list[str]
    confidence: float
    rationale: str


# Etkinlik tipi → kurulum eşlemesi (mock kuralları)
_SETUP_MAP = {
    "conference": ("classroom", ["coffee_break", "lunch", "water_station"]),
    "meeting": ("boardroom", ["coffee_break", "water_station"]),
    "wedding": ("banquet", ["dinner", "cocktail", "cake"]),
    "gala": ("banquet", ["dinner", "cocktail", "wine_package"]),
    "other": ("theater", ["coffee_break"]),
}


class EventIQAgent(BaseAgent):
    agent_name = "event_qi"
    model_provider = "deepseek"
    prompt_version = "1.0.0"

    async def _run(
        self, input_schema: EventIQInput, context=None, db=None, user=None
    ) -> EventIQOutput:
        setup, catering = _SETUP_MAP.get(input_schema.event_type, _SETUP_MAP["other"])
        # Kapasite payı: pax + %20 tampon
        capacity = int(input_schema.pax_count * 1.2)
        venue = "Balo Salonu A" if capacity >= 120 else "Toplantı Salonu B"
        return EventIQOutput(
            venue_suggestion=venue,
            setup_type=setup,
            capacity=capacity,
            catering_items=catering,
            confidence=0.85,
            rationale=f"{input_schema.event_type} için {input_schema.pax_count} kişi → {setup} düzeni, %20 kapasite tamponu.",
        )
