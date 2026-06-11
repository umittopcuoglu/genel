from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Text
from sqlalchemy.orm import mapped_column
from app.models.base import BaseModel


class AIInvocation(BaseModel):
    __tablename__ = "ai_invocations"

    agent_name: str = mapped_column(String(100))
    input_tokens: int = mapped_column(Integer, default=0)
    output_tokens: int = mapped_column(Integer, default=0)
    total_cost: Decimal = mapped_column(Numeric(10, 6), default=Decimal(0))
    latency_ms: int = mapped_column(Integer, default=0)
    status: str = mapped_column(String(20))
    error_message: str | None = mapped_column(Text, nullable=True)
    llm_response: str | None = mapped_column(Text, nullable=True)
    model_provider: str = mapped_column(String(50))
    prompt_version: str = mapped_column(String(20), default="1.0.0")
