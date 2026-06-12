from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.db import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_roles
from app.schemas.groups import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    RoomBlockCreate,
    RoomBlockResponse,
    EventCreate,
    EventResponse,
    GroupRoomingListCreate,
    GroupRoomingListResponse,
)
from app.services.groups_service import GroupsService
from typing import List

router = APIRouter(prefix="/api/v1/groups", tags=["groups"])


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Yeni grup oluştur (master folio otomatik)."""
    group = await GroupsService.create_group(db, group_data, current_user)
    return group


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: UUID,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Grup detaylarını getir (room blocks, events, rooming list dahil)."""
    group = await GroupsService.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grup bulunamadı")
    return group


@router.patch("/{group_id}/status", response_model=GroupResponse)
async def update_group_status(
    group_id: UUID,
    status_update: dict,
    current_user: dict = Depends(require_roles(["superadmin", "manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Grup durumunu güncelle (inquiry→confirmed→completed; cancelled her yerden)."""
    new_status = status_update.get("status")
    if new_status not in ["inquiry", "confirmed", "completed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Geçersiz durum"
        )

    try:
        group = await GroupsService.update_group_status(db, group_id, new_status, current_user)
    except ValueError as exc:
        # Geçersiz durum geçişi / yetersiz envanter → 422
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": {"code": "INVALID_STATUS_TRANSITION", "message": str(exc), "details": {}}},
        )
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grup bulunamadı")
    return group


@router.post("/{group_id}/room-blocks", response_model=RoomBlockResponse, status_code=status.HTTP_201_CREATED)
async def create_room_block(
    group_id: UUID,
    block_data: RoomBlockCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Grup için oda bloku ekle."""
    block = await GroupsService.create_room_block(db, group_id, block_data, current_user)
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grup bulunamadı")
    return block


@router.patch("/{group_id}/room-blocks/{block_id}/release", response_model=RoomBlockResponse)
async def release_room_block(
    group_id: UUID,
    block_id: UUID,
    current_user: dict = Depends(require_roles(["superadmin", "manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Oda bloğunu serbest bırak (release)."""
    block = await GroupsService.release_room_block(db, group_id, block_id, current_user)
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block bulunamadı")
    return block


@router.post("/{group_id}/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    group_id: UUID,
    event_data: EventCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "fb"])),
    db: AsyncSession = Depends(get_db),
):
    """Grup için etkinlik oluştur."""
    event = await GroupsService.create_event(db, group_id, event_data, current_user)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grup bulunamadı")
    return event


@router.post("/{group_id}/rooming-list/import", status_code=status.HTTP_201_CREATED)
async def import_rooming_list(
    group_id: UUID,
    rooming_list: List[GroupRoomingListCreate],
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Toplu rooming list import (CSV'den parse edilmiş)."""
    result = await GroupsService.import_rooming_list(db, group_id, rooming_list, current_user)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grup bulunamadı")
    return {"imported_count": result, "group_id": group_id}


@router.get("", response_model=List[GroupResponse])
async def list_groups(
    status_filter: str = Query(None),
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Tüm grupları listele (duruma göre filter)."""
    groups = await GroupsService.list_groups(db, status=status_filter)
    return groups


@router.get("/{group_id}/rooming-list", response_model=List[GroupRoomingListResponse])
async def get_rooming_list(
    group_id: UUID,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Grubun rooming list'ini getir."""
    rooming_list = await GroupsService.get_rooming_list(db, group_id)
    return rooming_list
