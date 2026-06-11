"""
Minibar router: ürün CRUD + odaya post (folio'ya fnb satırı).
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_roles
from app.models.user import User
from app.models.housekeeping import MinibarItem
from app.models.front_office import Stay, Room
from app.models.finance import Folio, FolioItem, FolioStatus, FolioItemType
from app.schemas.housekeeping import (
    MinibarPostRequest, MinibarItemCreate,
)

router = APIRouter()

TEMP_PREFIX = "/minibar"  # will be prefixed as /api/v1/minibar/...


def err(code: str, msg: str, status_code: int = 400, details: dict = None):
    raise HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": msg, "details": details or {}}}
    )


# ──── Minibar Item CRUD ────

@router.get("/minibar/items", response_model=list[dict],
            summary="Minibar ürün listesi")
async def list_minibar_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping", "frontdesk"])),
):
    stmt = select(MinibarItem).where(MinibarItem.deleted_at.is_(None)).order_by(MinibarItem.name)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return [
        {"id": str(i.id), "name": i.name, "price": str(i.price), "tax_rate": str(i.tax_rate)}
        for i in items
    ]


@router.post("/minibar/items", response_model=dict,
             status_code=201, summary="Minibar ürün ekle")
async def create_minibar_item(
    data: MinibarItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    item = MinibarItem(
        name=data.name,
        price=data.price,
        tax_rate=data.tax_rate,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": str(item.id), "name": item.name, "price": str(item.price), "tax_rate": str(item.tax_rate)}


# ──── Minibar Post ────

@router.post("/minibar/post", response_model=dict,
             status_code=201, summary="Minibar tüketimini post et")
async def post_minibar(
    data: MinibarPostRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping", "frontdesk"])),
):
    # Odada aktif konaklama var mı?
    stay_stmt = select(Stay).where(
        Stay.room_id == data.room_id,
        Stay.is_checked_in.is_(True),
        Stay.is_checked_out.is_(False),
        Stay.deleted_at.is_(None),
    )
    stay_result = await db.execute(stay_stmt)
    stay = stay_result.scalar_one_or_none()
    if not stay:
        err("NO_ACTIVE_STAY", f"Oda ({data.room_id}) için aktif konaklama bulunamadı", 409)

    # Folio'yu bul/yoksa oluştur
    folio_stmt = select(Folio).where(
        Folio.reservation_id == stay.reservation_id,
        Folio.deleted_at.is_(None),
    )
    folio_result = await db.execute(folio_stmt)
    folio = folio_result.scalar_one_or_none()
    if not folio:
        err("NO_FOLIO", "Rezervasyon için folio bulunamadı. Önce gece audit çalıştırın.", 409)

    if folio.status != FolioStatus.OPEN.value:
        err("FOLIO_CLOSED", "Folio kapalı olduğu için minibar post edilemez", 409)

    # Ürünleri post et
    posted_items = []
    total_posted = Decimal("0")

    for item_data in data.items:
        item_stmt = select(MinibarItem).where(
            MinibarItem.id == item_data.minibar_item_id,
            MinibarItem.deleted_at.is_(None),
        )
        item_result = await db.execute(item_stmt)
        minibar_item = item_result.scalar_one_or_none()
        if not minibar_item:
            err("MINIBAR_ITEM_NOT_FOUND",
                f"Minibar ürün bulunamadı: {item_data.minibar_item_id}", 404)

        folio_item = FolioItem(
            folio_id=folio.id,
            type=FolioItemType.FNB.value,
            description=f"{minibar_item.name} x{item_data.qty}",
            qty=item_data.qty,
            unit_price=minibar_item.price,
            tax_rate=minibar_item.tax_rate,
            posted_at=datetime.now(timezone.utc),
        )
        folio_item.total = folio_item.calculate_total()
        db.add(folio_item)

        posted_items.append(f"{minibar_item.name} x{item_data.qty}")
        total_posted += folio_item.total

    # Folio balances yenile
    await db.refresh(folio, ["items", "payments"])
    folio.recalculate()

    # Reservation.balance senkronizasyonu
    from app.models.front_office import Reservation
    res_stmt = select(Reservation).where(Reservation.id == folio.reservation_id)
    res_result = await db.execute(res_stmt)
    res = res_result.scalar_one_or_none()
    if res:
        res.balance = folio.balance

    await db.commit()

    return {
        "data": {
            "folio_id": str(folio.id),
            "posted_items": posted_items,
            "total_posted": str(total_posted),
        },
        "meta": {},
    }
