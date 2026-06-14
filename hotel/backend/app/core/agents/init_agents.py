from app.core.agents.registry import registry
from app.core.agents.revenue_qa import RevenueQAAgent
from app.core.agents.guest_ai import GuestAIAgent
from app.core.agents.insight_ai import InsightAIAgent
from app.core.agents.shift_ai import ShiftAIAgent
from app.core.agents.event_qi import EventIQAgent
from app.core.agents.tech_care import TechCareAgent
from app.core.agents.chef_iq import ChefIQAgent
from app.core.agents.secure_ai import SecureAIAgent
from app.core.agents.frontdesk_ai import FrontDeskAIAgent


def initialize_agents():
    """Register all agents on startup."""
    registry.register(RevenueQAAgent())
    registry.register(GuestAIAgent())
    registry.register(InsightAIAgent())
    # FrontDesk AI (temel — check-in asistanı)
    registry.register(FrontDeskAIAgent())
    # Faz 3 ajanları (EventIQ, TechCare, ChefIQ, SecureAI, ShiftAI)
    registry.register(ShiftAIAgent())
    registry.register(EventIQAgent())
    registry.register(TechCareAgent())
    registry.register(ChefIQAgent())
    registry.register(SecureAIAgent())
