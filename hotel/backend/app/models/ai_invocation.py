from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class AIInvocation(BaseModel):
    __tablename__ = "ai_invocations"

    agent_name: Mapped[str] = mapped_column(String(100))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=Decimal(0))
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20))
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_provider: Mapped[str] = mapped_column(String(50))
    prompt_version: Mapped[str] = mapped_column(String(20), default="1.0.0")
