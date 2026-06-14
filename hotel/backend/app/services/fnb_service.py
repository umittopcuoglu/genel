"""TASK-016 — F&B / POS servis katmanı."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.models.fnb import (
    POSOutlet, MenuItem, POSCheck, POSCheckItem, StockItem, StockMovement,
)
from app.models.finance import Folio, FolioItem
from app.schemas.fnb import (
    OutletCreate, MenuItemCreate, CheckCreate, CheckItemAdd,
    StockItemCreate, StockMovementCreate,
)


class FnbService:
    # ── Outlet ──
    @staticmethod
    async def create_outlet(db: AsyncSession, data: OutletCreate, current_user: dict) -> POSOutlet:
        outlet = POSOutlet(
            name=data.name,
            outlet_type=data.outlet_type,
            created_by=current_user.get("user_id"),
        )
        db.add(outlet)
        await db.commit()
        await db.refresh(outlet)
        return outlet

    @staticmethod
    async def list_outlets(db: AsyncSession) -> list[POSOutlet]:
        result = await db.execute(select(POSOutlet))
        return result.scalars().all()

    # ── Menu ──
    @staticmethod
    async def create_menu_item(db: AsyncSession, data: MenuItemCreate, current_user: dict) -> MenuItem:
        item = MenuItem(
            outlet_id=data.outlet_id,
            name=data.name,
            category=data.category,
            price=data.price,
            cost=data.cost,
            tax_rate=data.tax_rate,
            created_by=current_user.get("user_id"),
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def list_menu_items(db: AsyncSession, outlet_id: UUID | None = None) -> list[MenuItem]:
        stmt = select(MenuItem)
        if outlet_id:
            stmt = stmt.where(MenuItem.outlet_id == outlet_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_menu_item(db: AsyncSession, item_id: UUID) -> MenuItem | None:
        result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
        return result.scalar_one_or_none()

    # ── Check ──
    @staticmethod
    async def open_check(db: AsyncSession, data: CheckCreate, current_user: dict) -> POSCheck:
        check = POSCheck(
            outlet_id=data.outlet_id,
            table_no=data.table_no,
            room_no=data.room_no,
            notes=data.notes,
            status="open",
            total=Decimal("0"),
            opened_at=datetime.utcnow(),
            created_by=current_user.get("user_id"),
        )
        db.add(check)
        await db.commit()
        await db.refresh(check)
        return check

    @staticmethod
    async def get_check(db: AsyncSession, check_id: UUID) -> POSCheck | None:
        result = await db.execute(select(POSCheck).where(POSCheck.id == check_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def add_item(db: AsyncSession, check_id: UUID, data: CheckItemAdd, current_user: dict) -> POSCheck | None:
        check = await FnbService.get_check(db, check_id)
        if not check:
            return None
        if check.status != "open":
            raise ValueError("Adisyon kapalı; satır eklenemez")
        menu_item = await FnbService.get_menu_item(db, data.menu_item_id)
        if not menu_item:
            raise LookupError("Menü kalemi bulunamadı")

        line_total = (menu_item.price * data.qty)
        line = POSCheckItem(
            check_id=check.id,
            menu_item_id=menu_item.id,
            description=menu_item.name,
            qty=data.qty,
            unit_price=menu_item.price,
            total=line_total,
            created_by=current_user.get("user_id"),
        )
        db.add(line)
        check.total = (check.total or Decimal("0")) + line_total
        await db.commit()
        await db.refresh(check)
        return check

    @staticmethod
    async def close_check(db: AsyncSession, check_id: UUID, current_user: dict) -> POSCheck | None:
        check = await FnbService.get_check(db, check_id)
        if not check:
            return None
        if check.status == "closed":
            raise ValueError("Adisyon zaten kapalı")
        check.status = "closed"
        check.closed_at = datetime.utcnow()
        await db.commit()
        await db.refresh(check)
        return check

    @staticmethod
    async def post_room_charge(db: AsyncSession, check_id: UUID, folio_id: UUID, current_user: dict) -> POSCheck:
        """Adisyonu oda folio'suna 'fnb' satırı olarak yansıt (room charge)."""
        check = await FnbService.get_check(db, check_id)
        if not check:
            raise LookupError("Adisyon bulunamadı")

        result = await db.execute(select(Folio).where(Folio.id == folio_id))
        folio = result.scalar_one_or_none()
        if not folio:
            raise LookupError("Folio bulunamadı")
        if folio.status == "closed":
            raise ValueError("Folio kapalı; masraf yazılamaz")

        folio_item = FolioItem(
            folio_id=folio.id,
            type="fnb",
            description=f"F&B Adisyon #{str(check.id)[:8]}",
            qty=1,
            unit_price=check.total,
            tax_rate=Decimal("10"),
            total=check.total,
            posted_at=datetime.utcnow(),
            created_by=current_user.get("user_id"),
        )
        db.add(folio_item)
        folio.total = (folio.total or Decimal("0")) + check.total
        folio.balance = (folio.balance or Decimal("0")) + check.total
        check.folio_id = folio.id
        check.status = "closed"
        check.closed_at = datetime.utcnow()
        await db.commit()
        await db.refresh(check)
        return check

    # ── Stock ──
    @staticmethod
    async def create_stock_item(db: AsyncSession, data: StockItemCreate, current_user: dict) -> StockItem:
        item = StockItem(
            name=data.name,
            unit=data.unit,
            quantity=data.quantity,
            reorder_level=data.reorder_level,
            created_by=current_user.get("user_id"),
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def list_stock_items(db: AsyncSession) -> list[StockItem]:
        result = await db.execute(select(StockItem))
        return result.scalars().all()

    @staticmethod
    async def list_low_stock(db: AsyncSession) -> list[StockItem]:
        result = await db.execute(select(StockItem).where(StockItem.quantity <= StockItem.reorder_level))
        return result.scalars().all()

    @staticmethod
    async def move_stock(db: AsyncSession, data: StockMovementCreate, current_user: dict) -> StockItem:
        result = await db.execute(select(StockItem).where(StockItem.id == data.stock_item_id))
        item = result.scalar_one_or_none()
        if not item:
            raise LookupError("Stok kalemi bulunamadı")
        if data.movement_type not in ("in", "out"):
            raise ValueError("movement_type 'in' veya 'out' olmalı")
        if data.movement_type == "out" and item.quantity < data.quantity:
            raise ValueError("Yetersiz stok")

        delta = data.quantity if data.movement_type == "in" else -data.quantity
        item.quantity = (item.quantity or Decimal("0")) + delta
        movement = StockMovement(
            stock_item_id=item.id,
            movement_type=data.movement_type,
            quantity=data.quantity,
            reason=data.reason,
            moved_at=datetime.utcnow(),
            created_by=current_user.get("user_id"),
        )
        db.add(movement)
        await db.commit()
        await db.refresh(item)
        return item
