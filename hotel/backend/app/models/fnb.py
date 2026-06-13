"""
TASK-016 — F&B / POS modülü modelleri.
POS satış noktaları, menü, adisyon (check) + satırları, basit stok takibi.
Oda numarasına adisyon yazımı → aktif konaklama folio'suna fnb satırı (room charge).
"""
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric, Boolean, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.finance import Folio


class POSOutlet(BaseModel):
    """Satış noktası (restoran, bar, room-service)."""
    __tablename__ = "pos_outlets"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    outlet_type: Mapped[str] = mapped_column(String(30), nullable=False)  # restaurant, bar, room_service, cafe
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(15), default="active", nullable=False)

    menu_items: Mapped[list["MenuItem"]] = relationship("MenuItem", back_populates="outlet", lazy="selectin")
    checks: Mapped[list["POSCheck"]] = relationship("POSCheck", back_populates="outlet", lazy="selectin")


class MenuItem(BaseModel):
    """Menü kalemi (ürün)."""
    __tablename__ = "menu_items"

    outlet_id: Mapped[str] = mapped_column(Uuid, ForeignKey("pos_outlets.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # starter, main, dessert, beverage
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("10"), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    outlet: Mapped["POSOutlet"] = relationship("POSOutlet", back_populates="menu_items")


class POSCheck(BaseModel):
    """Adisyon başlık."""
    __tablename__ = "pos_checks"

    outlet_id: Mapped[str] = mapped_column(Uuid, ForeignKey("pos_outlets.id"), nullable=False)
    table_no: Mapped[str | None] = mapped_column(String(20), nullable=True)
    room_no: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(15), default="open", nullable=False)  # open, closed, voided
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    folio_id: Mapped[str | None] = mapped_column(Uuid, ForeignKey("folios.id"), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    outlet: Mapped["POSOutlet"] = relationship("POSOutlet", back_populates="checks")
    items: Mapped[list["POSCheckItem"]] = relationship("POSCheckItem", back_populates="check", lazy="selectin")


class POSCheckItem(BaseModel):
    """Adisyon satırı."""
    __tablename__ = "pos_check_items"

    check_id: Mapped[str] = mapped_column(Uuid, ForeignKey("pos_checks.id"), nullable=False)
    menu_item_id: Mapped[str] = mapped_column(Uuid, ForeignKey("menu_items.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)

    check: Mapped["POSCheck"] = relationship("POSCheck", back_populates="items")


class StockItem(BaseModel):
    """Basit stok kalemi."""
    __tablename__ = "stock_items"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)  # kg, lt, piece
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=Decimal("0"), nullable=False)
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=Decimal("0"), nullable=False)

    movements: Mapped[list["StockMovement"]] = relationship("StockMovement", back_populates="stock_item", lazy="selectin")


class StockMovement(BaseModel):
    """Stok hareketi (giriş/çıkış)."""
    __tablename__ = "stock_movements"

    stock_item_id: Mapped[str] = mapped_column(Uuid, ForeignKey("stock_items.id"), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(10), nullable=False)  # in, out
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    moved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    stock_item: Mapped["StockItem"] = relationship("StockItem", back_populates="movements")
