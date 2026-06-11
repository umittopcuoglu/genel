from abc import ABC, abstractmethod
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


class BaseAgent(ABC):
    agent_name: str
    model_provider: str = "deepseek"
    prompt_version: str = "1.0.0"

    @abstractmethod
    async def execute(
        self,
        input_schema: BaseModel,
        context: dict | None = None,
        db: AsyncSession | None = None,
        user: User | None = None,
    ) -> BaseModel:
        pass
