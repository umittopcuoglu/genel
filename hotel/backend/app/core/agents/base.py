from abc import ABC, abstractmethod
import logging
import time
from decimal import Decimal
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    agent_name: str
    model_provider: str = "deepseek"
    prompt_version: str = "1.0.0"

    @abstractmethod
    async def _run(
        self,
        input_schema: BaseModel,
        context: dict | None = None,
        db: AsyncSession | None = None,
        user: User | None = None,
    ) -> BaseModel:
        pass

    async def execute(
        self,
        input_schema: BaseModel,
        context: dict | None = None,
        db: AsyncSession | None = None,
        user: User | None = None,
    ) -> BaseModel:
        start = time.monotonic()
        try:
            result = await self._run(input_schema, context, db, user)
            elapsed_ms = int((time.monotonic() - start) * 1000)
            await self._log_invocation(db, elapsed_ms, "success")
            return result
        except Exception as e:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            await self._log_invocation(db, elapsed_ms, "error", str(e))
            raise

    async def _log_invocation(
        self, db: AsyncSession | None, latency_ms: int, status: str, error: str | None = None
    ) -> None:
        if db is None:
            return
        try:
            from app.models.ai_invocation import AIInvocation
            inv = AIInvocation(
                agent_name=self.agent_name,
                model_provider=self.model_provider,
                prompt_version=self.prompt_version,
                latency_ms=latency_ms,
                status=status,
                error_message=error,
                input_tokens=0,
                output_tokens=0,
                total_cost=Decimal(0),
            )
            db.add(inv)
            await db.commit()
        except Exception as e:
            logger.debug(f"AI invocation log failed: {e}")
