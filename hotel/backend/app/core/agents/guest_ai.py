from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.agents.base import BaseAgent
from app.core.llm import get_llm_client
from app.core.security.pii_masker import PIIMasker


class GuestAIChatInput(BaseModel):
    guest_name: str
    loyalty_tier: str
    message: str


class GuestAIChatOutput(BaseModel):
    message: str
    sentiment: str


class GuestAIAgent(BaseAgent):
    agent_name = "guest_ai"
    model_provider = "deepseek"
    prompt_version = "1.0.0"

    async def _run(
        self, input_schema: GuestAIChatInput, context=None, db=None, user=None
    ) -> GuestAIChatOutput:
        prompt = f"""
        Sen HotelOps misafir asistanısın.
        Misafir: {input_schema.guest_name}
        Loyalty seviyesi: {input_schema.loyalty_tier}
        Misafirin sorusu: "{input_schema.message}"

        Kurallar:
        - Samimi ve profesyonel ol
        - Teknik sorunlar için resepsiyon'u öner
        - Türkçe konuş
        - Kısa cevap (100-150 kelime)
        """

        masked_prompt, mask_map = PIIMasker.mask(prompt, context=context)

        llm_client = get_llm_client(self.model_provider)
        response = await llm_client.chat_completion(
            messages=[{"role": "user", "content": masked_prompt}],
            model="deepseek-chat",
            temperature=0.8,
            max_tokens=500,
        )

        llm_output = response["content"]
        unmasked_output = PIIMasker.unmask(llm_output, mask_map)
        sentiment = self._detect_sentiment(input_schema.message)

        return GuestAIChatOutput(message=unmasked_output, sentiment=sentiment)

    @staticmethod
    def _detect_sentiment(text: str) -> str:
        negative_words = ["kötü", "sorun", "çok kötü", "berbat", "şikayet"]
        positive_words = ["harika", "çok iyi", "mükemmel", "beğendim", "teşekkür"]

        text_lower = text.lower()
        if any(word in text_lower for word in negative_words):
            return "negative"
        if any(word in text_lower for word in positive_words):
            return "positive"
        return "neutral"
