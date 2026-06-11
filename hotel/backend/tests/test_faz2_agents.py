import pytest
from app.core.agents.revenue_qa import RevenueQAAgent, RevenueQAInput
from app.core.agents.guest_ai import GuestAIAgent, GuestAIChatInput
from app.core.agents.insight_ai import InsightAIAgent, InsightAIInput


@pytest.mark.asyncio
async def test_revenue_qa_agent():
    agent = RevenueQAAgent()
    assert agent.agent_name == "revenue_qa"
    assert agent.model_provider == "deepseek"

    input_data = RevenueQAInput(room_type_id="standard", forecast_horizon=7)
    output = await agent.execute(input_data)

    assert output.recommended_rate > 0
    assert output.confidence > 0
    assert len(output.rationale) > 0


@pytest.mark.asyncio
async def test_guest_ai_agent():
    agent = GuestAIAgent()
    assert agent.agent_name == "guest_ai"

    input_data = GuestAIChatInput(
        guest_name="Ahmet Yılmaz",
        loyalty_tier="silver",
        message="Odada sorun var",
    )
    output = await agent.execute(input_data)

    assert len(output.message) > 0
    assert output.sentiment in ["positive", "negative", "neutral"]


@pytest.mark.asyncio
async def test_guest_ai_sentiment_detection():
    agent = GuestAIAgent()

    assert agent._detect_sentiment("Çok kötü bir hizmet") == "negative"
    assert agent._detect_sentiment("Harika bir otel") == "positive"
    assert agent._detect_sentiment("Oda temiz") == "neutral"


@pytest.mark.asyncio
async def test_insight_ai_agent():
    agent = InsightAIAgent()
    assert agent.agent_name == "insight_ai"

    input_data = InsightAIInput(
        occupancy_recent=75.0,
        occupancy_previous=70.0,
        revpar_recent=550.0,
        revpar_previous=500.0,
    )
    output = await agent.execute(input_data)

    assert len(output.brief) > 0
    assert "%" in output.brief or "TL" in output.brief or "gün" in output.brief.lower()
