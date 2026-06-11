from app.core.agents.registry import registry
from app.core.agents.revenue_qa import RevenueQAAgent
from app.core.agents.guest_ai import GuestAIAgent
from app.core.agents.insight_ai import InsightAIAgent


def initialize_agents():
    """Register all agents on startup."""
    registry.register(RevenueQAAgent())
    registry.register(GuestAIAgent())
    registry.register(InsightAIAgent())
