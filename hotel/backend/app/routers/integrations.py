"""
Entegrasyon Ayarları router'ı — sadece superadmin/manager.
GİB e-Fatura, OTA, GDS, WhatsApp, IoT parametreleri çalışma zamanında yönetilir.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.user import User
from app.schemas.integration import (
    PARAM_SPECS,
    IntegrationCreate,
    IntegrationResponse,
    IntegrationTestResult,
    IntegrationUpdate,
)
from app.services.integration_service import IntegrationService

router = APIRouter(prefix="/api/v1/integrations", tags=["Entegrasyon Ayarları"])

ADMIN_ROLES = ["superadmin", "manager"]


@router.get("/specs")
async def get_param_specs(current_user: User = Depends(require_roles(ADMIN_ROLES))):
    """Tip başına beklenen parametre tanımları (frontend form üretimi)."""
    return PARAM_SPECS


@router.get("/connectors")
async def list_available_connectors(current_user: User = Depends(require_roles(ADMIN_ROLES))):
    """C4: Plugin Marketplace — kayıtlı tüm OTA connector'ları listele."""
    from app.services.connectors import available_connectors, get_connector

    items = []
    for code in available_connectors():
        cls = get_connector(code)
        items.append({
            "code": code,
            "name": getattr(cls, "display_name", code.title()),
            "class_name": cls.__name__ if cls else None,
            "category": "ota",
            "description": (cls.__doc__ or "").strip().split("\n")[0] if cls else "",
        })
    return {"available": items, "count": len(items)}


@router.post("", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    data: IntegrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN_ROLES)),
):
    """Yeni entegrasyon kaydı oluştur (parametreler şifreli saklanır)."""
    err = IntegrationService.validate_params(data.integration_type, data.params)
    if data.enabled and err:
        # Etkinleştirilecekse parametreler tam olmalı; taslak kayda izin ver
        raise HTTPException(status_code=422, detail=err)
    return await IntegrationService.create(db, data, str(current_user.id))


@router.get("", response_model=List[IntegrationResponse])
async def list_integrations(
    integration_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN_ROLES)),
):
    """Entegrasyon kayıtlarını listele (hassas alanlar maskeli)."""
    return await IntegrationService.list(db, integration_type)


@router.get("/{setting_id}", response_model=IntegrationResponse)
async def get_integration(
    setting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN_ROLES)),
):
    row = await IntegrationService.get_row(db, setting_id)
    if not row:
        raise HTTPException(status_code=404, detail="Entegrasyon kaydı bulunamadı.")
    return IntegrationService._to_dict(row)


@router.patch("/{setting_id}", response_model=IntegrationResponse)
async def update_integration(
    setting_id: UUID,
    data: IntegrationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN_ROLES)),
):
    """Kısmi güncelleme — maskeli gönderilen gizli değerler korunur."""
    row = await IntegrationService.get_row(db, setting_id)
    if not row:
        raise HTTPException(status_code=404, detail="Entegrasyon kaydı bulunamadı.")
    return await IntegrationService.update(db, row, data, str(current_user.id))


@router.delete("/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    setting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin"])),
):
    """Soft delete — sadece superadmin."""
    row = await IntegrationService.get_row(db, setting_id)
    if not row:
        raise HTTPException(status_code=404, detail="Entegrasyon kaydı bulunamadı.")
    await IntegrationService.soft_delete(db, row, str(current_user.id))


@router.post("/{setting_id}/test", response_model=IntegrationTestResult)
async def test_integration(
    setting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN_ROLES)),
):
    """Canlı bağlantı testi: IoT → TCP, diğerleri → HTTP erişilebilirlik."""
    row = await IntegrationService.get_row(db, setting_id)
    if not row:
        raise HTTPException(status_code=404, detail="Entegrasyon kaydı bulunamadı.")
    return await IntegrationService.test_connection(db, row)
