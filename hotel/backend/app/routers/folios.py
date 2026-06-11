"""
Folio (folyo) yönetimi: masraf yükleme, ödeme, kapatma, sorgulama.
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_roles
from app.models.user import User
from app.models.finance import (
    Folio, FolioItem, Payment,
    FolioStatus, PaymentStatus,
)
from app.models.front_office import Reservation
from app.schemas.finance import (
    FolioItemCreate, FolioPaymentCreate, FolioResponse, FolioListResponse,
)

router = APIRouter()


def err(code: str, msg: str, status_code: int = 400, details: dict = None):
    raise HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": msg, "details": details or {}}}
    )


async def _get_folio(db: AsyncSession, folio_id: uuid.UUID) -> Optional[Folio]:
    stmt = select(Folio).options(
        selectinload(Folio.items),
        selectinload(Folio.payments),
    ).where(Folio.id == folio_id, Folio.deleted_at.is_(None))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _refresh_folio_balances(db: AsyncSession, folio: Folio):
    await db.refresh(folio, ["items", "payments"])
    folio.recalculate()
    await db.flush()


@router.get("/folios/{folio_id}", response_model=FolioResponse,
            summary="Folio detayı (items + payments ile)")
async def get_folio(
    folio_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk", "accounting"])),
):
    folio = await _get_folio(db, folio_id)
    if not folio:
        err("NOT_FOUND", "Folio bulunamadı", 404)
    return folio


@router.get("/folios", response_model=FolioListResponse,
            summary="Folio listesi (filtre ile)")
async def list_folios(
    reservation_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200, alias="per_page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk", "accounting"])),
):
    stmt = select(Folio).options(
        selectinload(Folio.items),
        selectinload(Folio.payments),
    ).where(Folio.deleted_at.is_(None))

    if reservation_id:
        stmt = stmt.where(Folio.reservation_id == reservation_id)
    if status_filter:
        stmt = stmt.where(Folio.status == status_filter)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = stmt.order_by(Folio.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return FolioListResponse(
        data=items,
        meta={"page": page, "per_page": per_page, "total": total,
              "total_pages": (total + per_page - 1) // per_page}
    )


@router.post("/folios/{folio_id}/charge", response_model=FolioResponse,
             status_code=201, summary="Folio'ya masraf yükle")
async def charge_folio(
    folio_id: uuid.UUID,
    data: FolioItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk", "accounting"])),
):
    folio = await _get_folio(db, folio_id)
    if not folio:
        err("NOT_FOUND", "Folio bulunamadı", 404)
    if folio.status != FolioStatus.OPEN.value:
        err("FOLIO_CLOSED", "Folio kapalı olduğu için masraf eklenemez", 409)

    item = FolioItem(
        folio_id=folio.id,
        type=data.type,
        description=data.description,
        qty=data.qty,
        unit_price=data.unit_price,
        tax_rate=data.tax_rate,
        posted_at=datetime.now(timezone.utc),
    )
    item.total = item.calculate_total()

    db.add(item)
    await db.flush()
    await _refresh_folio_balances(db, folio)

    res_stmt = select(Reservation).where(Reservation.id == folio.reservation_id)
    res_result = await db.execute(res_stmt)
    res = res_result.scalar_one_or_none()
    if res:
        res.balance = folio.balance

    await db.commit()
    await db.refresh(folio, ["items", "payments"])
    return folio


@router.post("/folios/{folio_id}/payment", response_model=FolioResponse,
             status_code=201, summary="Folio'ya ödeme kaydet")
async def pay_folio(
    folio_id: uuid.UUID,
    data: FolioPaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk", "accounting"])),
):
    folio = await _get_folio(db, folio_id)
    if not folio:
        err("NOT_FOUND", "Folio bulunamadı", 404)

    if data.amount > folio.balance:
        err("OVERPAYMENT", f"Ödeme tutarı bakiye fazlası. Kalan bakiye: {folio.balance}",
            422, {"balance": str(folio.balance), "amount": str(data.amount)})

    payment = Payment(
        folio_id=folio.id,
        method=data.method,
        amount=data.amount,
        currency=data.currency or "TRY",
        ref=data.ref,
        status=PaymentStatus.COMPLETED.value,
    )
    db.add(payment)
    await db.flush()
    await _refresh_folio_balances(db, folio)

    res_stmt = select(Reservation).where(Reservation.id == folio.reservation_id)
    res_result = await db.execute(res_stmt)
    res = res_result.scalar_one_or_none()
    if res:
        res.balance = folio.balance

    await db.commit()
    await db.refresh(folio, ["items", "payments"])
    return folio


@router.post("/folios/{folio_id}/close", response_model=FolioResponse,
             summary="Folio kapat")
async def close_folio(
    folio_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "accounting"])),
):
    folio = await _get_folio(db, folio_id)
    if not folio:
        err("NOT_FOUND", "Folio bulunamadı", 404)

    await _refresh_folio_balances(db, folio)

    if folio.balance != 0:
        err("OUTSTANDING_BALANCE",
            f"Folio kapatılamaz. Kalan bakiye: {folio.balance}",
            409, {"balance": str(folio.balance)})

    folio.status = FolioStatus.CLOSED.value
    await db.commit()
    await db.refresh(folio, ["items", "payments"])
    return folio
