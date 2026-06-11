from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class ChartOfAccount(BaseModel):
    __tablename__ = "chart_of_accounts"

    account_code: Mapped[str] = mapped_column(String(20), unique=True)
    account_name: Mapped[str] = mapped_column(String(255))
    account_type: Mapped[str] = mapped_column(String(50))
    is_main_account: Mapped[bool] = mapped_column(Boolean, default=True)
    normal_balance: Mapped[str] = mapped_column(String(10))
    balance_sheet_order: Mapped[int] = mapped_column(Integer)
    income_statement_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
