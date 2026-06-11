"""
Rate Plan CRUD endpointleri.
Restrictions JSONB validasyonu.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_roles
from app.models.user import User
from app.models.reservation_ext import RatePlan
from app.schemas.rate_plan import (
    RatePlanCreate, RatePlanUpdate, RatePlanResponse, RatePlanListResponse,
)

router = APIRouter()

ALLOWED_RESTRICTION_KEYS = {"min_los", "max_los", "cta", "ctd", "closed", "min_stay_arrival", "max_stay_arrival"}


def err(code: str, msg: str, status: int = 400, details: dict = None):
    raise HTTPException(
        status_code=status,
        detail={"error": {"code": code, "message": msg, "details": details or {}}}
    )


@router.get("/rate-plans", response_model=RatePlanListResponse,
            summary="Rate plan listesi")
async def list_rate_plans(
    room_type_id: Optional[uuid.UUID] = Query(None),
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    stmt = select(RatePlan).options(selectinload(RatePlan.room_type)).where(RatePlan.deleted_at.is_(None))
    if room_type_id:
        stmt = stmt.where(RatePlan.room_type_id == room_type_id)
    if active_only:
        stmt = stmt.where(RatePlan.is_active.is_(True))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = stmt.order_by(RatePlan.code).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return RatePlanListResponse(
        data=items,
        meta={"page": page, "per_page": per_page, "total": total, "total_pages": (total + per_page - 1) // per_page}
    )


@router.post("/rate-plans", response_model=RatePlanResponse, status_code=201,
             summary="Rate plan olustur")
async def create_rate_plan(
    data: RatePlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    # Restrictions validasyonu
    if data.restrictions:
        unknown = set(data.restrictions.keys()) - ALLOWED_RESTRICTION_KEYS
        if unknown:
            err("INVALID_RESTRICTIONS", f"Bilinmeyen kisitlama anahtari: {', '.join(unknown)}", 422)

    # Code unique mi kontrol et
    stmt = select(func.count()).select_from(RatePlan).where(
        RatePlan.code == data.code, RatePlan.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    if result.scalar_one() > 0:
        err("DUPLICATE_CODE", f"'{data.code}' kodu zaten kullaniliyor", 409)

    rp = RatePlan(
        code=data.code,
        name=data.name,
        room_type_id=data.room_type_id,
        base_rate=data.base_rate,
        restrictions=data.restrictions,
        is_active=data.is_active,
    )
    db.add(rp)
    await db.commit()
    await db.refresh(rp)

    # Reload with room_type
    stmt2 = select(RatePlan).options(selectinload(RatePlan.room_type)).where(RatePlan.id == rp.id)
    r2 = await db.execute(stmt2)
    return r2.scalar_one()


@router.patch("/rate-plans/{rate_plan_id}", response_model=RatePlanResponse,
              summary="Rate plan guncelle")
async def update_rate_plan(
    rate_plan_id: uuid.UUID,
    data: RatePlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    stmt = select(RatePlan).options(selectinload(RatePlan.room_type)).where(
        RatePlan.id == rate_plan_id, RatePlan.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    rp = result.scalar_one_or_none()
    if not rp:
        err("NOT_FOUND", "Rate plan bulunamadi", 404)

    update_data = data.model_dump(exclude_unset=True)

    # Restrictions validasyonu
    if "restrictions" in update_data and update_data["restrictions"] is not None:
        unknown = set(update_data["restrictions"].keys()) - ALLOWED_RESTRICTION_KEYS
        if unknown:
            err("INVALID_RESTRICTIONS", f"Bilinmeyen kisitlama anahtari: {', '.join(unknown)}", 422)

    for key, value in update_data.items():
        setattr(rp, key, value)

    await db.commit()
    await db.refresh(rp)
    return rp


@router.get("/rate-plans/{rate_plan_id}", response_model=RatePlanResponse,
            summary="Rate plan detayi")
async def get_rate_plan(
    rate_plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    stmt = select(RatePlan).options(selectinload(RatePlan.room_type)).where(
        RatePlan.id == rate_plan_id, RatePlan.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    rp = result.scalar_one_or_none()
    if not rp:
        err("NOT_FOUND", "Rate plan bulunamadi", 404)
    return rp
