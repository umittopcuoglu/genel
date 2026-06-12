"""
Voice Control router: Alexa/Google webhook, entegrasyon, intent mapping endpoint'leri.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.user import User
from app.schemas.voice import (
    VoiceIntegrationCreate,
    VoiceIntegrationResponse,
    VoiceIntegrationUpdate,
    VoiceCommandResponse,
    VoiceSessionResponse,
    VoiceInteractionResponse,
    VoiceIntentsMappingCreate,
    VoiceIntentsMappingResponse,
)
from app.services.voice_service import VoiceService

router = APIRouter(prefix="/api/v1/voice", tags=["Voice Control"])


# ── Integration Endpoints ──

@router.post("/integrations", response_model=VoiceIntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    data: VoiceIntegrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Yeni sesli asistan entegrasyonu oluştur."""
    return await VoiceService.create_integration(db, data, {"user_id": str(current_user.id)})


@router.get("/integrations", response_model=List[VoiceIntegrationResponse])
async def list_integrations(
    room_id: UUID = Query(None),
    provider: str = Query(None, description="alexa, google_assistant"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance", "frontdesk"])),
):
    """Sesli asistan entegrasyonlarını listele."""
    return await VoiceService.list_integrations(db, room_id=room_id, provider=provider)


@router.get("/integrations/{integration_id}", response_model=VoiceIntegrationResponse)
async def get_integration(
    integration_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance", "frontdesk"])),
):
    """Entegrasyon detayını getir."""
    integration = await VoiceService.get_integration(db, integration_id)
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entegrasyon bulunamadı")
    return integration


@router.patch("/integrations/{integration_id}", response_model=VoiceIntegrationResponse)
async def update_integration(
    integration_id: UUID,
    data: VoiceIntegrationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Entegrasyon bilgilerini güncelle."""
    integration = await VoiceService.update_integration(db, integration_id, data, {"user_id": str(current_user.id)})
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entegrasyon bulunamadı")
    return integration


# ── Webhook Endpoints ──

@router.post("/webhook/alexa")
async def alexa_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Alexa skill webhook'u."""
    payload = await request.json()
    return await VoiceService.handle_alexa_webhook(db, payload, {"user_id": str(current_user.id)})


@router.post("/webhook/google")
async def google_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "frontdesk"])),
):
    """Google Actions webhook'u."""
    payload = await request.json()
    return await VoiceService.handle_google_webhook(db, payload, {"user_id": str(current_user.id)})


# ── Intents Mapping Endpoints ──

@router.post("/intents", response_model=VoiceIntentsMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_intent_mapping(
    data: VoiceIntentsMappingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager"])),
):
    """Yeni intent eşleştirmesi oluştur."""
    return await VoiceService.create_intent_mapping(db, data, {"user_id": str(current_user.id)})


@router.get("/intents", response_model=List[VoiceIntentsMappingResponse])
async def list_intent_mappings(
    provider: str = Query(None, description="alexa, google_assistant"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Intent eşleştirmelerini listele."""
    return await VoiceService.list_intent_mappings(db, provider=provider)


# ── Command / Session / Interaction Log Endpoints ──

@router.get("/commands", response_model=List[VoiceCommandResponse])
async def list_commands(
    integration_id: UUID = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Sesli komut loglarını listele."""
    return await VoiceService.list_commands(db, integration_id=integration_id, limit=limit)


@router.get("/sessions", response_model=List[VoiceSessionResponse])
async def list_sessions(
    integration_id: UUID = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Sesli oturumları listele."""
    return await VoiceService.list_sessions(db, integration_id=integration_id, limit=limit)


@router.get("/interactions", response_model=List[VoiceInteractionResponse])
async def list_interactions(
    integration_id: UUID = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["superadmin", "manager", "maintenance"])),
):
    """Webhook etkileşim loglarını listele."""
    return await VoiceService.list_interactions(db, integration_id=integration_id, limit=limit)
