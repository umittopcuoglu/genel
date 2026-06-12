"""F&B / POS router'ı."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.fnb import Check, CheckStatus, MenuItem, Outlet
from app.models.user import User
from app.services.fnb_service import FnBService

router = APIRouter(prefix="/api/v1/fnb", tags=["F&B"])

POS_ROLES = ["superadmin", "manager", "frontdesk", "fnb"]
MGR_ROLES = ["superadmin", "manager"]


# ── Schemas ──

class OutletCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    kind: str = "restaurant"
    open_time: Optional[str] = None
    close_time: Optional[str] = None


class OutletResponse(BaseModel):
    id: UUID
    name: str
    kind: str
    is_active: bool
    open_time: Optional[str]
    close_time: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class MenuItemCreate(BaseModel):
    outlet_id: UUID
    name: str = Field(min_length=2, max_length=150)
    category: str = "main"
    price: Decimal = Field(gt=0)
    kdv_rate: Decimal = Decimal("0.10")


class MenuItemResponse(BaseModel):
    id: UUID
    outlet_id: UUID
    name: str
    category: str
    price: Decimal
    kdv_rate: Decimal
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CheckCreate(BaseModel):
    outlet_id: UUID
    table_no: Optional[str] = None
    guest_id: Optional[UUID] = None


class CheckItemAdd(BaseModel):
    menu_item_id: UUID
    qty: int = Field(default=1, ge=1, le=99)


class PostToFolioRequest(BaseModel):
    folio_id: UUID


class CheckItemResponse(BaseModel):
    id: UUID
    menu_item_id: UUID
    name_snapshot: str
    qty: int
    unit_price: Decimal
    kdv_rate: Decimal
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class CheckResponse(BaseModel):
    id: UUID
    outlet_id: UUID
    table_no: Optional[str]
    guest_id: Optional[UUID]
    folio_id: Optional[UUID]
    status: str
    subtotal: Decimal
    kdv_total: Decimal
    total: Decimal
    items: List[CheckItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ── Outlet ──

@router.post("/outlets", response_model=OutletResponse, status_code=status.HTTP_201_CREATED)
async def create_outlet(
    payload: OutletCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGR_ROLES)),
):
    o = Outlet(**payload.model_dump())
    db.add(o)
    await db.commit()
    await db.refresh(o)
    return OutletResponse.model_validate(o)


@router.get("/outlets", response_model=List[OutletResponse])
async def list_outlets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(POS_ROLES)),
):
    res = await db.execute(select(Outlet).where(Outlet.deleted_at.is_(None)))
    return [OutletResponse.model_validate(o) for o in res.scalars().all()]


# ── Menu Items ──

@router.post(
    "/menu-items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED
)
async def create_menu_item(
    payload: MenuItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGR_ROLES)),
):
    mi = MenuItem(**payload.model_dump())
    db.add(mi)
    await db.commit()
    await db.refresh(mi)
    return MenuItemResponse.model_validate(mi)


@router.get("/outlets/{outlet_id}/menu", response_model=List[MenuItemResponse])
async def list_menu(
    outlet_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(POS_ROLES)),
):
    res = await db.execute(
        select(MenuItem).where(
            MenuItem.outlet_id == outlet_id, MenuItem.deleted_at.is_(None)
        )
    )
    return [MenuItemResponse.model_validate(m) for m in res.scalars().all()]


# ── Checks ──

@router.post("/checks", response_model=CheckResponse, status_code=status.HTTP_201_CREATED)
async def create_check(
    payload: CheckCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(POS_ROLES)),
):
    check = Check(**payload.model_dump())
    db.add(check)
    await db.commit()
    await db.refresh(check, attribute_names=["items"])
    return CheckResponse.model_validate(check)


@router.post("/checks/{check_id}/items", response_model=CheckResponse)
async def add_item(
    check_id: UUID,
    payload: CheckItemAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(POS_ROLES)),
):
    try:
        check = await FnBService.add_item(db, check_id, payload.menu_item_id, payload.qty)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await db.refresh(check, attribute_names=["items"])
    return CheckResponse.model_validate(check)


@router.post("/checks/{check_id}/post-to-folio", response_model=CheckResponse)
async def post_to_folio(
    check_id: UUID,
    payload: PostToFolioRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(POS_ROLES)),
):
    try:
        check = await FnBService.post_to_folio(db, check_id, payload.folio_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await db.refresh(check, attribute_names=["items"])
    return CheckResponse.model_validate(check)


@router.post("/checks/{check_id}/settle-cash", response_model=CheckResponse)
async def settle_cash(
    check_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(POS_ROLES)),
):
    try:
        check = await FnBService.settle_cash(db, check_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await db.refresh(check, attribute_names=["items"])
    return CheckResponse.model_validate(check)


@router.post("/checks/{check_id}/void", response_model=CheckResponse)
async def void(
    check_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(POS_ROLES)),
):
    try:
        check = await FnBService.void(db, check_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await db.refresh(check, attribute_names=["items"])
    return CheckResponse.model_validate(check)


@router.get("/checks/{check_id}", response_model=CheckResponse)
async def get_check(
    check_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(POS_ROLES)),
):
    check = await db.get(Check, check_id)
    if check is None:
        raise HTTPException(status_code=404, detail="Adisyon bulunamadı")
    await db.refresh(check, attribute_names=["items"])
    return CheckResponse.model_validate(check)
