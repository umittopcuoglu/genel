"""
Console router: Zincir/Property yönetimi, PropertyUser, Sync Log, Konsolide Rapor.
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
from app.schemas.chain import (
    ChainCreate,
    ChainResponse,
    ChainUpdate,
    PropertyCreate,
    PropertyResponse,
    PropertyUpdate,
    PropertyUserCreate,
    PropertyUserResponse,
    PropertyUserUpdate,
    PropertySyncLogResponse,
    ConsolidatedReportResponse,
    ConsolidatedReportGenerate,
)
from app.services.chain_service import ChainService
from app.services.consolidation_service import ConsolidationService

router = APIRouter(prefix="/api/v1/console", tags=["Chain / Multi-Property"])


# ── Chain Endpoints ──

@router.post("/chains", response_model=ChainResponse, status_code=status.HTTP_201_CREATED)
async def create_chain(
    data: ChainCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Yeni otel zinciri oluştur."""
    return await ChainService.create_chain(db, data, {"user_id": str(current_user.id)})


@router.get("/chains", response_model=List[ChainResponse])
async def list_chains(
    is_active: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Zincirleri listele."""
    return await ChainService.list_chains(db, is_active=is_active)


@router.get("/chains/{chain_id}", response_model=ChainResponse)
async def get_chain(
    chain_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Zincir detayını getir."""
    chain = await ChainService.get_chain(db, chain_id)
    if not chain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zincir bulunamadı")
    return chain


@router.patch("/chains/{chain_id}", response_model=ChainResponse)
async def update_chain(
    chain_id: UUID,
    data: ChainUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Zincir bilgilerini güncelle."""
    chain = await ChainService.update_chain(db, chain_id, data, {"user_id": str(current_user.id)})
    if not chain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zincir bulunamadı")
    return chain


# ── Property Endpoints ──

@router.post("/properties", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Yeni mülk/otel oluştur."""
    return await ChainService.create_property(db, data, {"user_id": str(current_user.id)})


@router.get("/properties", response_model=List[PropertyResponse])
async def list_properties(
    chain_id: UUID = Query(None),
    city: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Mülkleri listele."""
    return await ChainService.list_properties(db, chain_id=chain_id, city=city)


@router.get("/properties/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Mülk detayını getir."""
    property = await ChainService.get_property(db, property_id)
    if not property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mülk bulunamadı")
    return property


@router.patch("/properties/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: UUID,
    data: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Mülk bilgilerini güncelle."""
    property = await ChainService.update_property(db, property_id, data, {"user_id": str(current_user.id)})
    if not property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mülk bulunamadı")
    return property


@router.get("/properties/{property_id}/kpis")
async def get_property_kpis(
    property_id: UUID,
    report_date: date = Query(default=date.today()),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Mülk KPI'larını getir."""
    return await ConsolidationService.compute_property_kpis(db, property_id, report_date)


# ── PropertyUser Endpoints ──

@router.post("/property-users", response_model=PropertyUserResponse, status_code=status.HTTP_201_CREATED)
async def create_property_user(
    data: PropertyUserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Mülke kullanıcı ataması yap."""
    return await ChainService.create_property_user(db, data, {"user_id": str(current_user.id)})


@router.get("/property-users", response_model=List[PropertyUserResponse])
async def list_property_users(
    property_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Mülk kullanıcı atamalarını listele."""
    return await ChainService.list_property_users(db, property_id=property_id)


@router.patch("/property-users/{pu_id}", response_model=PropertyUserResponse)
async def update_property_user(
    pu_id: UUID,
    data: PropertyUserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Mülk kullanıcı atamasını güncelle."""
    pu = await ChainService.update_property_user(db, pu_id, data, {"user_id": str(current_user.id)})
    if not pu:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atama bulunamadı")
    return pu


# ── Sync Log Endpoints ──

@router.get("/sync-logs", response_model=List[PropertySyncLogResponse])
async def list_sync_logs(
    property_id: UUID = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Senkronizasyon loglarını listele."""
    return await ChainService.list_sync_logs(db, property_id=property_id, limit=limit)


# ── Consolidated Report Endpoints ──

@router.post("/reports/generate", response_model=ConsolidatedReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    data: ConsolidatedReportGenerate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Konsolide rapor oluştur."""
    return await ChainService.generate_report(db, data, {"user_id": str(current_user.id)})


@router.get("/reports", response_model=List[ConsolidatedReportResponse])
async def list_reports(
    chain_id: UUID = Query(None),
    report_type: str = Query(None, description="daily, weekly, monthly, quarterly, yearly"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Konsolide raporları listele."""
    return await ChainService.list_reports(db, chain_id=chain_id, report_type=report_type, limit=limit)


@router.get("/chains/{chain_id}/kpis")
async def get_chain_kpis(
    chain_id: UUID,
    report_date: date = Query(default=date.today()),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Zincir geneli KPI'ları getir."""
    return await ConsolidationService.compute_chain_kpis(db, chain_id, report_date)
