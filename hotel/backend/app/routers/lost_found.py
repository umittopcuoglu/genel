"""
Lost & Found router: kayıp eşya kaydı + iade.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.core.db import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_roles
from app.models.user import User
from app.models.housekeeping import LostFound
from app.schemas.housekeeping import (
    LostFoundCreate, LostFoundReturn, LostFoundResponse,
)

router = APIRouter()


def err(code: str, msg: str, status_code: int = 400, details: dict = None):
    raise HTTPException(
        status_code=status_code,
        detail={"error": {"code": code, "message": msg, "details": details or {}}}
    )


@router.get("/lost-found", response_model=list[LostFoundResponse],
            summary="Kayıp eşya listesi")
async def list_lost_found(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200, alias="per_page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping", "frontdesk"])),
):
    stmt = select(LostFound).where(LostFound.deleted_at.is_(None))
    if status_filter:
        stmt = stmt.where(LostFound.status == status_filter)
    stmt = stmt.order_by(LostFound.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/lost-found", response_model=LostFoundResponse,
             status_code=201, summary="Kayıp eşya kaydet")
async def create_lost_found(
    data: LostFoundCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping", "frontdesk"])),
):
    item = LostFound(
        room_id=data.room_id,
        found_by=current_user.id,
        item_description=data.item_description,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/lost-found/{item_id}/return", response_model=LostFoundResponse,
              summary="Kayıp eşyayı iade et")
async def return_lost_found(
    item_id: uuid.UUID,
    data: LostFoundReturn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping", "frontdesk"])),
):
    stmt = select(LostFound).where(LostFound.id == item_id, LostFound.deleted_at.is_(None))
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        err("NOT_FOUND", "Kayıp eşya kaydı bulunamadı", 404)

    item.status = "returned"
    item.returned_to = data.returned_to
    item.returned_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(item)
    return item
