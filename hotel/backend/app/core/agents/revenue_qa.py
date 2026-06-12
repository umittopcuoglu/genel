from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.agents.base import BaseAgent
from app.core.llm import get_llm_client
from app.core.security.pii_masker import PIIMasker


class RevenueQAInput(BaseModel):
    room_type_id: str
    forecast_horizon: int = 7


class RevenueQAOutput(BaseModel):
    recommended_rate: float
    rationale: str
    confidence: float


class RevenueQAAgent(BaseAgent):
    agent_name = "revenue_qa"
    model_provider = "deepseek"
    prompt_version = "1.0.0"

    async def _run(
        self, input_schema: RevenueQAInput, context=None, db=None, user=None
    ) -> RevenueQAOutput:
        prompt = f"""
        Siz HotelOps sisteminin gelir danışmanısınız.
        Oda tipi: {input_schema.room_type_id}
        Tahmin ufku: {input_schema.forecast_horizon} gün

        İstatistiksel veriler:
        - Geçmiş ortalama ücret: 400 TL
        - Mevcut ücret: 450 TL
        - Doluluk tahmini: %68
        - Pazar trendi: yükselen
        - Rakip ort.: 420 TL

        Ücret önerinizi sunun. Yanıt: "Önerilen ücret: XXX TL çünkü..."
        """

        masked_prompt, mask_map = PIIMasker.mask(prompt, context=context)

        llm_client = get_llm_client(self.model_provider)
        response = await llm_client.chat_completion(
            messages=[{"role": "user", "content": masked_prompt}],
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=500,
        )

        llm_output = response["content"]
        unmasked_output = PIIMasker.unmask(llm_output, mask_map)

        extracted_rate = self._extract_rate(unmasked_output)

        return RevenueQAOutput(
            recommended_rate=extracted_rate or 450.0,
            rationale=unmasked_output[:200],
            confidence=0.85,
        )

    @staticmethod
    def _extract_rate(text: str) -> float | None:
        import re

        match = re.search(r"Önerilen.*?(\d+)", text)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                return None
        return None
