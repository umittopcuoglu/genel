"""
Computer Vision router: CV Model, Inspection, Defect, Inventory endpoint'leri.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.user import User
from app.schemas.cv import (
    CVModelCreate,
    CVModelResponse,
    RoomInspectionCreate,
    RoomInspectionResponse,
    RoomInspectionUpdate,
    InspectionDefectResponse,
    DefectVerify,
    InventorySnapshotResponse,
)
from app.services.cv_service import CVService

router = APIRouter(prefix="/api/v1/cv", tags=["Computer Vision"])


# ── CV Model Endpoints ──

@router.post("/models", response_model=CVModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    data: CVModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Yeni CV modeli kaydet."""
    return await CVService.create_model(db, data, {"user_id": str(current_user.id)})


@router.get("/models", response_model=List[CVModelResponse])
async def list_models(
    model_type: str = Query(None, description="inspection, object_detection, defect_classification"),
    is_active: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """CV modellerini listele."""
    return await CVService.list_models(db, model_type=model_type, is_active=is_active)


# ── Inspection Endpoints ──

@router.post("/inspections", response_model=RoomInspectionResponse, status_code=status.HTTP_201_CREATED)
async def create_inspection(
    data: RoomInspectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping", "maintenance"])),
):
    """Yeni oda denetimi başlat."""
    return await CVService.create_inspection(db, data, {"user_id": str(current_user.id)})


@router.get("/inspections", response_model=List[RoomInspectionResponse])
async def list_inspections(
    room_id: UUID = Query(None),
    status: str = Query(None, description="pending, in_progress, completed, failed"),
    inspection_type: str = Query(None, description="daily, deep_clean, pre_arrival, post_departure"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping", "maintenance"])),
):
    """Denetimleri listele."""
    return await CVService.list_inspections(
        db, room_id=room_id, status=status, inspection_type=inspection_type
    )


@router.get("/inspections/{inspection_id}", response_model=RoomInspectionResponse)
async def get_inspection(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping", "maintenance"])),
):
    """Denetim detayını getir."""
    inspection = await CVService.get_inspection(db, inspection_id)
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denetim bulunamadı")
    return inspection


@router.post("/inspections/{inspection_id}/run")
async def run_inspection(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping", "maintenance"])),
):
    """CV analizini çalıştır (mock)."""
    result = await CVService.run_inspection(db, inspection_id, {"user_id": str(current_user.id)})
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denetim bulunamadı")
    return {
        "inspection_id": str(inspection_id),
        "status": "completed",
        "score": float(result.score),
        "defects_found": len(result.defects),
        "defects": result.defects,
        "inventory": result.inventory_items,
    }


@router.patch("/inspections/{inspection_id}", response_model=RoomInspectionResponse)
async def update_inspection(
    inspection_id: UUID,
    data: RoomInspectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping", "maintenance"])),
):
    """Denetim bilgilerini güncelle."""
    inspection = await CVService.update_inspection(db, inspection_id, data, {"user_id": str(current_user.id)})
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denetim bulunamadı")
    return inspection


# ── Defect Endpoints ──

@router.get("/inspections/{inspection_id}/defects", response_model=List[InspectionDefectResponse])
async def list_defects(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping", "maintenance"])),
):
    """Denetim kusurlarını listele."""
    return await CVService.list_defects(db, inspection_id)


@router.post("/defects/{defect_id}/verify", response_model=InspectionDefectResponse)
async def verify_defect(
    defect_id: UUID,
    data: DefectVerify,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping"])),
):
    """Kusuru doğrula/reddet."""
    defect = await CVService.verify_defect(db, defect_id, data, {"user_id": str(current_user.id)})
    if not defect:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kusur bulunamadı")
    return defect


# ── Inventory Endpoints ──

@router.get("/inspections/{inspection_id}/inventory", response_model=List[InventorySnapshotResponse])
async def list_inventory(
    inspection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "housekeeping", "maintenance"])),
):
    """Denetim envanterini listele."""
    return await CVService.list_inventory(db, inspection_id)
