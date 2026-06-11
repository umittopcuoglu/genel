from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.agents.base import BaseAgent
from app.core.llm import get_llm_client
from app.core.security.pii_masker import PIIMasker


class InsightAIInput(BaseModel):
    occupancy_recent: float = 68.5
    occupancy_previous: float = 65.0
    revpar_recent: float = 525.0
    revpar_previous: float = 500.0


class InsightAIOutput(BaseModel):
    brief: str


class InsightAIAgent(BaseAgent):
    agent_name = "insight_ai"
    model_provider = "deepseek"
    prompt_version = "1.0.0"

    async def execute(
        self, input_schema: InsightAIInput, context=None, db=None, user=None
    ) -> InsightAIOutput:
        prompt = f"""
        Sen HotelOps yönetici asistanısın.

        KPI Özeti (Son 7 gün vs Önceki Ay):
        - Doluluk: {input_schema.occupancy_recent}% (vs {input_schema.occupancy_previous}%)
        - RevPAR: {input_schema.revpar_recent} TL (vs {input_schema.revpar_previous} TL)

        Görev: Kısa sabah özeti hazırla (maksimum 300 kelime).
        - Hangi alanlar dikkat gerektirir?
        - Temel tavsiyeleri sun

        Yanıt: Yapılandırılmış (başlık, noktalar, tavsiyeler)
        """

        masked_prompt, mask_map = PIIMasker.mask(prompt, context=context)

        llm_client = get_llm_client(self.model_provider)
        response = await llm_client.chat_completion(
            messages=[{"role": "user", "content": masked_prompt}],
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=1500,
        )

        llm_output = response["content"]
        unmasked_output = PIIMasker.unmask(llm_output, mask_map)

        return InsightAIOutput(brief=unmasked_output)
