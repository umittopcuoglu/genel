from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from app.core.db import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_roles
from app.schemas.maintenance import (
    AssetCreate, AssetResponse,
    WorkOrderCreate, WorkOrderResponse, WorkOrderStatusUpdate,
    PreventiveMaintenanceCreate, PreventiveMaintenanceResponse,
    MaintenanceLogCreate, MaintenanceLogResponse,
)
from app.services.maintenance_service import MaintenanceService
from typing import List

router = APIRouter(prefix="/api/v1/maintenance", tags=["maintenance"])


@router.post("/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset_data: AssetCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "maintenance"])),
    db: AsyncSession = Depends(get_db),
):
    """Yeni varlık (ekipman) ekle."""
    asset = await MaintenanceService.create_asset(db, asset_data, current_user)
    return asset


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Varlık detaylarını getir."""
    asset = await MaintenanceService.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Varlık bulunamadı")
    return asset


@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
    db: AsyncSession = Depends(get_db),
):
    """Tüm varlıkları listele."""
    assets = await MaintenanceService.list_assets(db)
    return assets


@router.post("/work-orders", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_work_order(
    order_data: WorkOrderCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "maintenance", "housekeeping"])),
    db: AsyncSession = Depends(get_db),
):
    """Yeni iş emri aç."""
    work_order = await MaintenanceService.create_work_order(db, order_data, current_user)
    return work_order


@router.get("/work-orders/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order(
    work_order_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """İş emri detaylarını getir."""
    work_order = await MaintenanceService.get_work_order(db, work_order_id)
    if not work_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İş emri bulunamadı")
    return work_order


@router.get("/work-orders", response_model=List[WorkOrderResponse])
async def list_work_orders(
    status_filter: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """İş emirlerini listele (duruma göre filtrele)."""
    work_orders = await MaintenanceService.list_work_orders(db, status=status_filter)
    return work_orders


@router.patch("/work-orders/{work_order_id}/status", response_model=WorkOrderResponse)
async def update_work_order_status(
    work_order_id: UUID,
    status_update: WorkOrderStatusUpdate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "maintenance"])),
    db: AsyncSession = Depends(get_db),
):
    """İş emri durumunu güncelle."""
    work_order = await MaintenanceService.update_work_order_status(
        db, work_order_id, status_update.status, status_update.notes, current_user
    )
    if not work_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İş emri bulunamadı")
    return work_order


@router.patch("/work-orders/{work_order_id}/assign", response_model=WorkOrderResponse)
async def assign_work_order(
    work_order_id: UUID,
    assignment: dict,
    current_user: dict = Depends(require_roles(["superadmin", "manager"])),
    db: AsyncSession = Depends(get_db),
):
    """İş emrini personele ata."""
    assigned_to = assignment.get("assigned_to")
    work_order = await MaintenanceService.assign_work_order(db, work_order_id, assigned_to, current_user)
    if not work_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İş emri bulunamadı")
    return work_order


@router.post("/preventive-maintenance", response_model=PreventiveMaintenanceResponse, status_code=status.HTTP_201_CREATED)
async def create_preventive(
    pm_data: PreventiveMaintenanceCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "maintenance"])),
    db: AsyncSession = Depends(get_db),
):
    """Preventif bakım planı oluştur."""
    pm = await MaintenanceService.create_preventive_maintenance(db, pm_data, current_user)
    return pm


@router.get("/preventive-maintenance/due", response_model=List[PreventiveMaintenanceResponse])
async def get_due_maintenance(
    db: AsyncSession = Depends(get_db),
):
    """Vadesi gelen preventif bakımları getir."""
    pm_list = await MaintenanceService.get_due_maintenance(db)
    return pm_list


@router.post("/logs", response_model=MaintenanceLogResponse, status_code=status.HTTP_201_CREATED)
async def log_maintenance(
    log_data: MaintenanceLogCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "maintenance"])),
    db: AsyncSession = Depends(get_db),
):
    """Yapılan bakım işlemini kaydet."""
    log = await MaintenanceService.create_maintenance_log(db, log_data, current_user)
    return log


@router.get("/logs/{work_order_id}", response_model=List[MaintenanceLogResponse])
async def get_work_order_logs(
    work_order_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """İş emrinin bakım geçmişini getir."""
    logs = await MaintenanceService.get_work_order_logs(db, work_order_id)
    return logs
