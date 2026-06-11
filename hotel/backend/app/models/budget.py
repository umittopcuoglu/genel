from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class Budget(BaseModel):
    __tablename__ = "budgets"

    department: Mapped[str] = mapped_column(String(100))
    budget_year: Mapped[int] = mapped_column(Integer)
    budget_month: Mapped[int] = mapped_column(Integer)
    budgeted_revenue: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    budgeted_expense: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    actual_revenue: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    actual_expense: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    variance_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")
