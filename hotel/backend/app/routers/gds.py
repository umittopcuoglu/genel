"""
GDS Integration router: Channel, Reservation, Rate Mapping, Sync Log endpoint'leri.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from typing import List

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.user import User
from app.schemas.gds import (
    GDSChannelCreate,
    GDSChannelResponse,
    GDSChannelUpdate,
    GDSReservationResponse,
    GDSReservationSync,
    GDSReservationUpdate,
    GDSRateMappingCreate,
    GDSRateMappingResponse,
    GDSRateMappingUpdate,
    GDSSyncLogResponse,
)
from app.services.gds_service import GDSService

router = APIRouter(prefix="/api/v1/gds", tags=["GDS Integration"])


# ── Channel Endpoints ──

@router.post("/channels", response_model=GDSChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    data: GDSChannelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Yeni GDS/OTA kanalı oluştur."""
    return await GDSService.create_channel(db, data, {"user_id": str(current_user.id)})


@router.get("/channels", response_model=List[GDSChannelResponse])
async def list_channels(
    provider: str = Query(None, description="Provider filtresi (amadeus, sabre, booking)"),
    is_active: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """GDS kanallarını listele."""
    return await GDSService.list_channels(db, provider=provider, is_active=is_active)


@router.get("/channels/{channel_id}", response_model=GDSChannelResponse)
async def get_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Kanal detayını getir."""
    channel = await GDSService.get_channel(db, channel_id)
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kanal bulunamadı")
    return channel


@router.patch("/channels/{channel_id}", response_model=GDSChannelResponse)
async def update_channel(
    channel_id: UUID,
    data: GDSChannelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Kanal bilgilerini güncelle."""
    channel = await GDSService.update_channel(db, channel_id, data, {"user_id": str(current_user.id)})
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kanal bulunamadı")
    return channel


# ── Reservation Endpoints ──

@router.post("/reservations/sync", response_model=GDSReservationResponse, status_code=status.HTTP_201_CREATED)
async def sync_reservation(
    data: GDSReservationSync,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """GDS'den gelen rezervasyonu senkronize et."""
    return await GDSService.sync_reservation(db, data, {"user_id": str(current_user.id)})


@router.get("/reservations", response_model=List[GDSReservationResponse])
async def list_reservations(
    channel_id: UUID = Query(None),
    status: str = Query(None, description="pending, synced, modified, cancelled, error"),
    date_from: date = Query(None),
    date_to: date = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """GDS rezervasyonlarını listele."""
    return await GDSService.list_reservations(
        db, channel_id=channel_id, status=status, date_from=date_from, date_to=date_to
    )


@router.get("/reservations/{reservation_id}", response_model=GDSReservationResponse)
async def get_reservation(
    reservation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """GDS rezervasyon detayını getir."""
    reservation = await GDSService.get_reservation(db, reservation_id)
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rezervasyon bulunamadı")
    return reservation


@router.patch("/reservations/{reservation_id}", response_model=GDSReservationResponse)
async def update_reservation(
    reservation_id: UUID,
    data: GDSReservationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """GDS rezervasyon durumunu güncelle."""
    reservation = await GDSService.update_reservation(
        db, reservation_id, data, {"user_id": str(current_user.id)}
    )
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rezervasyon bulunamadı")
    return reservation


# ── Rate Mapping Endpoints ──

@router.post("/rate-mappings", response_model=GDSRateMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_rate_mapping(
    data: GDSRateMappingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """GDS-otel rate plan eşleştirmesi oluştur."""
    return await GDSService.create_rate_mapping(db, data, {"user_id": str(current_user.id)})


@router.get("/rate-mappings", response_model=List[GDSRateMappingResponse])
async def list_rate_mappings(
    channel_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Rate mapping'leri listele."""
    return await GDSService.list_rate_mappings(db, channel_id=channel_id)


@router.patch("/rate-mappings/{mapping_id}", response_model=GDSRateMappingResponse)
async def update_rate_mapping(
    mapping_id: UUID,
    data: GDSRateMappingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Rate mapping güncelle."""
    mapping = await GDSService.update_rate_mapping(
        db, mapping_id, data, {"user_id": str(current_user.id)}
    )
    if not mapping:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rate mapping bulunamadı")
    return mapping


# ── Sync Log Endpoints ──

@router.get("/sync-logs", response_model=List[GDSSyncLogResponse])
async def list_sync_logs(
    channel_id: UUID = Query(None),
    action: str = Query(None, description="search, book, cancel, modify, availability_update, rate_update"),
    status: str = Query(None, description="success, failed, pending"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Senkronizasyon loglarını listele."""
    return await GDSService.list_sync_logs(
        db, channel_id=channel_id, action=action, status=status, limit=limit
    )
