"""Güvenlik & KVKK router'ı."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.security import AccessLog, DataSubjectRequest, KVKKConsent
from app.models.user import User
from app.services.security_service import SecurityService

router = APIRouter(prefix="/api/v1/security", tags=["Güvenlik & KVKK"])

ALL_ROLES = ["superadmin", "manager", "frontdesk", "security"]
DPO_ROLES = ["superadmin", "manager", "dpo"]


# ── Access ──

class AccessLogRequest(BaseModel):
    door_code: str
    method: str = "card"
    granted: bool = True
    user_id: Optional[UUID] = None
    guest_id: Optional[UUID] = None
    reason: Optional[str] = None


class AccessLogResponse(BaseModel):
    id: UUID
    door_code: str
    user_id: Optional[UUID]
    guest_id: Optional[UUID]
    method: str
    granted: bool
    reason: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.post(
    "/access-logs", response_model=AccessLogResponse, status_code=status.HTTP_201_CREATED
)
async def log_access(
    req: AccessLogRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ALL_ROLES)),
):
    log = await SecurityService.log_access(
        db,
        door_code=req.door_code,
        method=req.method,
        granted=req.granted,
        user_id=req.user_id,
        guest_id=req.guest_id,
        reason=req.reason,
    )
    return AccessLogResponse.model_validate(log)


@router.get("/access-logs", response_model=List[AccessLogResponse])
async def list_access(
    door_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ALL_ROLES)),
):
    stmt = select(AccessLog).where(AccessLog.deleted_at.is_(None))
    if door_code:
        stmt = stmt.where(AccessLog.door_code == door_code)
    stmt = stmt.order_by(AccessLog.created_at.desc()).limit(200)
    res = await db.execute(stmt)
    return [AccessLogResponse.model_validate(r) for r in res.scalars().all()]


# ── KVKK Consent ──

class ConsentGrantRequest(BaseModel):
    guest_id: UUID
    purpose: str
    text_version: Optional[str] = None


class ConsentResponse(BaseModel):
    id: UUID
    guest_id: UUID
    purpose: str
    granted: bool
    granted_at: datetime
    revoked_at: Optional[datetime]
    text_version: Optional[str]

    model_config = ConfigDict(from_attributes=True)


@router.post("/kvkk/consents", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def grant_consent(
    req: ConsentGrantRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(DPO_ROLES)),
):
    try:
        c = await SecurityService.grant_consent(
            db, guest_id=req.guest_id, purpose=req.purpose, text_version=req.text_version
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ConsentResponse.model_validate(c)


@router.post("/kvkk/consents/{consent_id}/revoke", response_model=ConsentResponse)
async def revoke_consent(
    consent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(DPO_ROLES)),
):
    try:
        c = await SecurityService.revoke_consent(db, consent_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ConsentResponse.model_validate(c)


@router.get("/kvkk/guests/{guest_id}/consents", response_model=List[ConsentResponse])
async def list_consents(
    guest_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(DPO_ROLES)),
):
    res = await db.execute(
        select(KVKKConsent)
        .where(KVKKConsent.guest_id == guest_id, KVKKConsent.deleted_at.is_(None))
        .order_by(KVKKConsent.created_at.desc())
    )
    return [ConsentResponse.model_validate(c) for c in res.scalars().all()]


# ── Data Subject Requests ──

class DSRRequest(BaseModel):
    guest_id: UUID
    request_type: str = Field(pattern="^(access|erase|rectify|portability)$")
    notes: Optional[str] = None


class DSRResponse(BaseModel):
    id: UUID
    guest_id: UUID
    request_type: str
    status: str
    response_payload: Optional[dict]
    completed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.post("/kvkk/requests", response_model=DSRResponse, status_code=status.HTTP_201_CREATED)
async def open_request(
    req: DSRRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(DPO_ROLES)),
):
    try:
        r = await SecurityService.open_request(
            db, guest_id=req.guest_id, request_type=req.request_type, notes=req.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return DSRResponse.model_validate(r)


@router.post("/kvkk/requests/{request_id}/fulfill", response_model=DSRResponse)
async def fulfill(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(DPO_ROLES)),
):
    try:
        r = await SecurityService.fulfill_request(db, request_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return DSRResponse.model_validate(r)


@router.get("/kvkk/requests", response_model=List[DSRResponse])
async def list_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(DPO_ROLES)),
):
    res = await db.execute(
        select(DataSubjectRequest)
        .where(DataSubjectRequest.deleted_at.is_(None))
        .order_by(DataSubjectRequest.created_at.desc())
    )
    return [DSRResponse.model_validate(r) for r in res.scalars().all()]
