"""TASK-017 — Güvenlik & Erişim Kontrol & KVKK router (prefix /api/v1/security)."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from app.core.db import get_db
from app.core.rbac import require_roles
from app.schemas.security import (
    DoorLockCreate, DoorLockResponse,
    KeyCardCreate, KeyCardResponse,
    AccessLogCreate, AccessLogResponse,
    IncidentCreate, IncidentStatusUpdate, IncidentResponse,
    KVKKConsentCreate, KVKKConsentResponse,
    DataAccessRequestCreate, DataAccessRequestResponse,
)
from app.services.security_service import SecurityService

router = APIRouter(prefix="/api/v1/security", tags=["Security & KVKK"])


# ── Door Locks ──
@router.post("/door-locks", response_model=DoorLockResponse, status_code=status.HTTP_201_CREATED)
async def create_door_lock(
    data: DoorLockCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Kapı kilidi ekle."""
    return await SecurityService.create_door_lock(db, data, current_user)


@router.get("/door-locks", response_model=List[DoorLockResponse])
async def list_door_locks(
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Kapı kilidi envanteri."""
    return await SecurityService.list_door_locks(db)


# ── Key Cards ──
@router.post("/key-cards", response_model=KeyCardResponse, status_code=status.HTTP_201_CREATED)
async def issue_card(
    data: KeyCardCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Anahtar kartı üret (check-in)."""
    return await SecurityService.issue_card(db, data, current_user)


@router.get("/key-cards", response_model=List[KeyCardResponse])
async def list_cards(
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Anahtar kartlarını listele."""
    return await SecurityService.list_cards(db)


@router.patch("/key-cards/{card_id}/revoke", response_model=KeyCardResponse)
async def revoke_card(
    card_id: UUID,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Kartı iptal et (check-out)."""
    card = await SecurityService.revoke_card(db, card_id, current_user)
    if not card:
        raise HTTPException(status_code=404, detail="Kart bulunamadı")
    return card


# ── Access Logs ──
@router.post("/access-logs", response_model=AccessLogResponse, status_code=status.HTTP_201_CREATED)
async def log_access(
    data: AccessLogCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Erişim kaydı oluştur."""
    return await SecurityService.log_access(db, data, current_user)


@router.get("/access-logs", response_model=List[AccessLogResponse])
async def list_access_logs(
    result_filter: str = Query(None, description="granted veya denied"),
    current_user: dict = Depends(require_roles(["superadmin", "manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Erişim günlüğü sorgula."""
    return await SecurityService.list_access_logs(db, result_filter)


# ── Incidents ──
@router.post("/incidents", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    data: IncidentCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """Güvenlik olayı kaydı aç."""
    return await SecurityService.create_incident(db, data, current_user)


@router.get("/incidents", response_model=List[IncidentResponse])
async def list_incidents(
    current_user: dict = Depends(require_roles(["superadmin", "manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Güvenlik olaylarını listele."""
    return await SecurityService.list_incidents(db)


@router.patch("/incidents/{incident_id}/status", response_model=IncidentResponse)
async def update_incident_status(
    incident_id: UUID,
    data: IncidentStatusUpdate,
    current_user: dict = Depends(require_roles(["superadmin", "manager"])),
    db: AsyncSession = Depends(get_db),
):
    """Olay durumunu güncelle."""
    valid = ["open", "investigating", "resolved", "closed"]
    if data.status not in valid:
        raise HTTPException(status_code=422, detail={"error": {"code": "INVALID_STATUS", "message": "Geçersiz durum", "details": {"valid": valid}}})
    incident = await SecurityService.update_incident_status(db, incident_id, data.status, current_user)
    if not incident:
        raise HTTPException(status_code=404, detail="Olay bulunamadı")
    return incident


# ── KVKK Consents ──
@router.post("/kvkk/consents", response_model=KVKKConsentResponse, status_code=status.HTTP_201_CREATED)
async def create_consent(
    data: KVKKConsentCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """KVKK rıza kaydı oluştur."""
    return await SecurityService.create_consent(db, data, current_user)


@router.get("/kvkk/consents", response_model=List[KVKKConsentResponse])
async def list_consents(
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """KVKK rıza kayıtlarını listele."""
    return await SecurityService.list_consents(db)


@router.patch("/kvkk/consents/{consent_id}/withdraw", response_model=KVKKConsentResponse)
async def withdraw_consent(
    consent_id: UUID,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
    db: AsyncSession = Depends(get_db),
):
    """KVKK rızasını geri çek."""
    consent = await SecurityService.withdraw_consent(db, consent_id, current_user)
    if not consent:
        raise HTTPException(status_code=404, detail="Rıza kaydı bulunamadı")
    return consent


# ── KVKK Data Requests ──
@router.post("/kvkk/data-requests", response_model=DataAccessRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_data_request(
    data: DataAccessRequestCreate,
    current_user: dict = Depends(require_roles(["superadmin", "manager", "frontdesk", "guest"])),
    db: AsyncSession = Depends(get_db),
):
    """KVKK veri erişim/silme talebi oluştur."""
    return await SecurityService.create_data_request(db, data, current_user)


@router.get("/kvkk/data-requests", response_model=List[DataAccessRequestResponse])
async def list_data_requests(
    current_user: dict = Depends(require_roles(["superadmin", "manager"])),
    db: AsyncSession = Depends(get_db),
):
    """KVKK veri taleplerini listele."""
    return await SecurityService.list_data_requests(db)


@router.patch("/kvkk/data-requests/{request_id}/complete", response_model=DataAccessRequestResponse)
async def complete_data_request(
    request_id: UUID,
    current_user: dict = Depends(require_roles(["superadmin", "manager"])),
    db: AsyncSession = Depends(get_db),
):
    """KVKK veri talebini tamamla (anonimleştirme akışı)."""
    req = await SecurityService.complete_data_request(db, request_id, current_user)
    if not req:
        raise HTTPException(status_code=404, detail="Talep bulunamadı")
    return req
