"""F&B / POS modelleri: Outlet, MenuItem, Check, CheckItem."""
import enum
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Boolean, ForeignKey, Uuid, Integer, Index
from sqlalchemy.types import Numeric as SA_Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class CheckStatus(str, enum.Enum):
    OPEN = "open"
    PAID = "paid"
    VOIDED = "voided"
    POSTED_TO_FOLIO = "posted_to_folio"


class Outlet(BaseModel):
    """Restoran / Bar / Havuz Bar / Lobby Cafe vb."""
    __tablename__ = "fnb_outlets"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), nullable=False, default="restaurant")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    open_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # "07:00"
    close_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)


class MenuItem(BaseModel):
    __tablename__ = "fnb_menu_items"

    outlet_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("fnb_outlets.id"), index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="main")
    price: Mapped[Decimal] = mapped_column(SA_Decimal(10, 2), nullable=False)
    kdv_rate: Mapped[Decimal] = mapped_column(SA_Decimal(4, 2), nullable=False, default=Decimal("0.10"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Check(BaseModel):
    """Adisyon — siparişler buraya bağlanır, oda hesabına aktarılabilir."""
    __tablename__ = "fnb_checks"

    outlet_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("fnb_outlets.id"), index=True)
    table_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    guest_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("guests.id"), nullable=True
    )
    folio_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("folios.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=CheckStatus.OPEN.value)
    subtotal: Mapped[Decimal] = mapped_column(SA_Decimal(12, 2), nullable=False, default=0)
    kdv_total: Mapped[Decimal] = mapped_column(SA_Decimal(12, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(SA_Decimal(12, 2), nullable=False, default=0)

    items: Mapped[list["CheckItem"]] = relationship(
        "CheckItem", back_populates="check", cascade="all, delete-orphan"
    )


class CheckItem(BaseModel):
    __tablename__ = "fnb_check_items"

    check_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("fnb_checks.id"), index=True)
    menu_item_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("fnb_menu_items.id"))
    name_snapshot: Mapped[str] = mapped_column(String(150), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(SA_Decimal(10, 2), nullable=False)
    kdv_rate: Mapped[Decimal] = mapped_column(SA_Decimal(4, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(SA_Decimal(12, 2), nullable=False)

    check: Mapped["Check"] = relationship("Check", back_populates="items")
