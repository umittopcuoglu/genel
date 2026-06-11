import pytest
from pydantic import BaseModel
from app.core.agents.base import BaseAgent
from app.core.agents.registry import registry
from app.core.llm.client import MockLLMClient, get_llm_client
from app.core.llm.pricing import calc_cost
from app.core.llm.prompt_loader import PromptLoader
from app.core.security.pii_masker import PIIMasker


class MockAgent(BaseAgent):
    agent_name = "test_agent"

    async def execute(self, input_schema: BaseModel, context=None, db=None, user=None):
        return {"result": "test"}


class TestAgentRegistry:
    def test_register_agent(self):
        agent = MockAgent()
        registry.register(agent)
        retrieved = registry.get("test_agent")
        assert retrieved is not None
        assert retrieved.agent_name == "test_agent"

    def test_list_agents(self):
        agents = registry.list_agents()
        assert "test_agent" in agents


class TestLLMClient:
    @pytest.mark.asyncio
    async def test_mock_llm_client(self):
        client = MockLLMClient()
        response = await client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model="mock",
        )
        assert "content" in response
        assert response["content"] == "Mock LLM response for testing purposes."

    def test_get_llm_client_mock(self, monkeypatch):
        monkeypatch.setenv("ENABLE_LLM_MOCK", "true")
        client = get_llm_client()
        assert isinstance(client, MockLLMClient)


class TestPIIMasking:
    def test_mask_email(self):
        text = "Contact: john.doe@example.com"
        masked, mask_map = PIIMasker.mask(text)
        assert "john.doe@example.com" not in masked
        assert "[MASKED_EMAIL_0]" in masked

    def test_mask_phone(self):
        text = "Call me at +905001234567"
        masked, mask_map = PIIMasker.mask(text)
        assert "+905001234567" not in masked
        assert "[MASKED_TELEFON_0]" in masked

    def test_unmask(self):
        text = "Contact: john.doe@example.com"
        masked, mask_map = PIIMasker.mask(text)
        unmasked = PIIMasker.unmask(masked, mask_map)
        assert unmasked == text


class TestPricing:
    def test_deepseek_pricing(self):
        cost = calc_cost("deepseek", "deepseek-chat", 100, 50)
        assert cost > 0
        expected = (100 * 0.14 / 1_000_000) + (50 * 0.28 / 1_000_000)
        assert abs(cost - expected) < 0.0001

    def test_openai_pricing(self):
        cost = calc_cost("openai", "gpt-4", 100, 50)
        assert cost > 0


class TestPromptLoader:
    def test_load_prompt(self):
        prompt = PromptLoader.load("revenue_qa")
        assert len(prompt) > 0
        assert "gelir" in prompt.lower() or "ücret" in prompt.lower()

    def test_load_nonexistent_prompt(self):
        with pytest.raises(FileNotFoundError):
            PromptLoader.load("nonexistent_agent")
