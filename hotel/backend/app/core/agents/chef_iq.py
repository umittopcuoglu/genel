"""
TASK-016 — ChefIQ AI: Ürün talep tahmini + menü kâr/popülerlik içgörüsü.
Mock-first: basit trend çarpanı ile deterministik tahmin.
"""
from pydantic import BaseModel
from app.core.agents.base import BaseAgent


class ChefIQInput(BaseModel):
    item_name: str = "Izgara Levrek"
    recent_sales: int = 100
    is_weekend: bool = False


class ChefIQOutput(BaseModel):
    item_name: str
    forecast_demand: int
    recommended_stock: int
    confidence: float
    rationale: str


class ChefIQAgent(BaseAgent):
    agent_name = "chef_iq"
    model_provider = "deepseek"
    prompt_version = "1.0.0"

    async def execute(
        self, input_schema: ChefIQInput, context=None, db=None, user=None
    ) -> ChefIQOutput:
        # Hafta sonu talebi %35 artar (mock kural)
        multiplier = 1.35 if input_schema.is_weekend else 1.05
        forecast = int(input_schema.recent_sales * multiplier)
        # Önerilen stok: tahmin + %15 emniyet payı
        recommended = int(forecast * 1.15)
        return ChefIQOutput(
            item_name=input_schema.item_name,
            forecast_demand=forecast,
            recommended_stock=recommended,
            confidence=0.78,
            rationale=(
                f"{'Hafta sonu' if input_schema.is_weekend else 'Hafta içi'} çarpanı "
                f"({multiplier}x) ile {input_schema.recent_sales} → {forecast}; "
                f"%15 emniyet payı eklendi."
            ),
        )
