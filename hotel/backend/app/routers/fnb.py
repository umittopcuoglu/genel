"""TASK-016 — F&B / POS router (prefix /api/v1/fnb)."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from app.core.db import get_db
from app.core.rbac import require_roles
from app.schemas.fnb import (
    OutletCreate, OutletResponse,
    MenuItemCreate, MenuItemResponse,
    CheckCreate, CheckItemAdd, CheckResponse,
    RoomChargeRequest,
    StockItemCreate, StockItemResponse, StockMovementCreate,
)
from app.services.fnb_service import FnbService

router = APIRouter(prefix="/api/v1/fnb", tags=["F&B"])


# ── Outlets ──
@router.post("/outlets", response_model=OutletResponse, status_code=status.HTTP_201_CREATED)
async def create_outlet(
    data: OutletCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "fb"])),
    db: AsyncSession = Depends(get_db),
):
    """Yeni satış noktası ekle."""
    return await FnbService.create_outlet(db, data, current_user)


@router.get("/outlets", response_model=List[OutletResponse])
async def list_outlets(db: AsyncSession = Depends(get_db)):
    """Satış noktalarını listele."""
    return await FnbService.list_outlets(db)


# ── Menu ──
@router.post("/menu-items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    data: MenuItemCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "fb"])),
    db: AsyncSession = Depends(get_db),
):
    """Menüye kalem ekle."""
    return await FnbService.create_menu_item(db, data, current_user)


@router.get("/menu-items", response_model=List[MenuItemResponse])
async def list_menu_items(
    outlet_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Menü kalemlerini listele (outlet'e göre filtrele)."""
    return await FnbService.list_menu_items(db, outlet_id)


# ── Checks ──
@router.post("/checks", response_model=CheckResponse, status_code=status.HTTP_201_CREATED)
async def open_check(
    data: CheckCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "fb", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Adisyon aç."""
    return await FnbService.open_check(db, data, current_user)


@router.get("/checks/{check_id}", response_model=CheckResponse)
async def get_check(check_id: UUID, db: AsyncSession = Depends(get_db)):
    """Adisyon detayı."""
    check = await FnbService.get_check(db, check_id)
    if not check:
        raise HTTPException(status_code=404, detail="Adisyon bulunamadı")
    return check


@router.post("/checks/{check_id}/items", response_model=CheckResponse)
async def add_check_item(
    check_id: UUID,
    data: CheckItemAdd,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "fb", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Adisyona satır ekle."""
    try:
        check = await FnbService.add_item(db, check_id, data, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"error": {"code": "CHECK_CLOSED", "message": str(exc), "details": {}}})
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if not check:
        raise HTTPException(status_code=404, detail="Adisyon bulunamadı")
    return check


@router.post("/checks/{check_id}/close", response_model=CheckResponse)
async def close_check(
    check_id: UUID,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "fb", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Adisyonu kapat."""
    try:
        check = await FnbService.close_check(db, check_id, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"error": {"code": "ALREADY_CLOSED", "message": str(exc), "details": {}}})
    if not check:
        raise HTTPException(status_code=404, detail="Adisyon bulunamadı")
    return check


@router.post("/checks/{check_id}/room-charge", response_model=CheckResponse)
async def room_charge(
    check_id: UUID,
    data: RoomChargeRequest,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "fb", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Adisyonu oda folio'suna 'fnb' satırı olarak yansıt (room charge)."""
    try:
        check = await FnbService.post_room_charge(db, check_id, data.folio_id, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail={"error": {"code": "FOLIO_CLOSED", "message": str(exc), "details": {}}})
    return check


# ── Stock ──
@router.post("/stock-items", response_model=StockItemResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_item(
    data: StockItemCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "fb"])),
    db: AsyncSession = Depends(get_db),
):
    """Stok kalemi ekle."""
    return await FnbService.create_stock_item(db, data, current_user)


@router.get("/stock-items", response_model=List[StockItemResponse])
async def list_stock_items(db: AsyncSession = Depends(get_db)):
    """Stok kalemlerini listele (low_stock işaretli)."""
    items = await FnbService.list_stock_items(db)
    return [
        StockItemResponse(
            id=i.id, name=i.name, unit=i.unit, quantity=i.quantity,
            reorder_level=i.reorder_level, low_stock=i.quantity <= i.reorder_level,
        )
        for i in items
    ]


@router.get("/stock-items/low", response_model=List[StockItemResponse])
async def list_low_stock(db: AsyncSession = Depends(get_db)):
    """Düşük stok uyarısı listesi."""
    items = await FnbService.list_low_stock(db)
    return [
        StockItemResponse(
            id=i.id, name=i.name, unit=i.unit, quantity=i.quantity,
            reorder_level=i.reorder_level, low_stock=True,
        )
        for i in items
    ]


@router.post("/stock-movements", response_model=StockItemResponse)
async def move_stock(
    data: StockMovementCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "fb"])),
    db: AsyncSession = Depends(get_db),
):
    """Stok hareketi (giriş/çıkış)."""
    try:
        item = await FnbService.move_stock(db, data, current_user)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": {"code": "STOCK_ERROR", "message": str(exc), "details": {}}})
    return StockItemResponse(
        id=item.id, name=item.name, unit=item.unit, quantity=item.quantity,
        reorder_level=item.reorder_level, low_stock=item.quantity <= item.reorder_level,
    )
