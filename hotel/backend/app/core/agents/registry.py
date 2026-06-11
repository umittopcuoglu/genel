from app.core.agents.base import BaseAgent


class AgentRegistry:
    _agents: dict[str, BaseAgent] = {}

    @classmethod
    def register(cls, agent: BaseAgent) -> None:
        cls._agents[agent.agent_name] = agent

    @classmethod
    def get(cls, agent_name: str) -> BaseAgent | None:
        return cls._agents.get(agent_name)

    @classmethod
    def list_agents(cls) -> dict[str, BaseAgent]:
        return cls._agents.copy()


registry = AgentRegistry()
