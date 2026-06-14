"""CRM router'ı: Guest 360, Segment, Campaign, Notes, Communication."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.crm import Campaign, CommunicationLog, GuestNote, Segment
from app.models.front_office import Guest
from app.models.user import User
from app.schemas.crm import (
    CampaignCreate,
    CampaignResponse,
    CommunicationLogCreate,
    CommunicationLogResponse,
    Guest360Response,
    GuestNoteCreate,
    GuestNoteResponse,
    SegmentCreate,
    SegmentResponse,
    SegmentUpdate,
)
from app.services.crm_service import CRMService

router = APIRouter(prefix="/api/v1/crm", tags=["CRM"])

MGMT_ROLES = ["superadmin", "manager", "frontdesk", "accounting"]
ADMIN_ROLES = ["superadmin", "manager"]


# ── Guest 360 ──

@router.get("/guests/{guest_id}/360", response_model=Guest360Response)
async def guest_360(
    guest_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGMT_ROLES)),
):
    try:
        return await CRMService.guest_360(db, guest_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Segments ──

@router.post("/segments", response_model=SegmentResponse, status_code=status.HTTP_201_CREATED)
async def create_segment(
    payload: SegmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN_ROLES)),
):
    seg = Segment(**payload.model_dump())
    db.add(seg)
    await db.commit()
    await db.refresh(seg)
    return seg


@router.get("/segments", response_model=List[SegmentResponse])
async def list_segments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGMT_ROLES)),
):
    res = await db.execute(select(Segment).where(Segment.deleted_at.is_(None)).order_by(Segment.created_at.desc()))
    return list(res.scalars().all())


@router.patch("/segments/{seg_id}", response_model=SegmentResponse)
async def update_segment(
    seg_id: UUID,
    payload: SegmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN_ROLES)),
):
    seg = await db.get(Segment, seg_id)
    if seg is None or seg.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Segment bulunamadı")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(seg, k, v)
    await db.commit()
    await db.refresh(seg)
    return seg


@router.post("/segments/{seg_id}/preview")
async def preview_segment(
    seg_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGMT_ROLES)),
):
    seg = await db.get(Segment, seg_id)
    if seg is None:
        raise HTTPException(status_code=404, detail="Segment bulunamadı")
    guests = await CRMService.evaluate_segment(db, seg.criteria or {})
    return {
        "segment_id": seg.id,
        "match_count": len(guests),
        "sample": [
            {"id": str(g.id), "name": f"{g.first_name} {g.last_name}", "email": g.email}
            for g in guests[:20]
        ],
    }


# ── Campaigns ──

@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN_ROLES)),
):
    cmp_ = Campaign(**payload.model_dump())
    db.add(cmp_)
    await db.commit()
    await db.refresh(cmp_)
    return cmp_


@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGMT_ROLES)),
):
    res = await db.execute(
        select(Campaign).where(Campaign.deleted_at.is_(None)).order_by(Campaign.created_at.desc())
    )
    return list(res.scalars().all())


@router.post("/campaigns/{cmp_id}/send", response_model=CampaignResponse)
async def send_campaign(
    cmp_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(ADMIN_ROLES)),
):
    cmp_ = await db.get(Campaign, cmp_id)
    if cmp_ is None or cmp_.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Kampanya bulunamadı")
    try:
        return await CRMService.send_campaign(db, cmp_)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Guest Notes ──

@router.post("/notes", response_model=GuestNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: GuestNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGMT_ROLES)),
):
    note = GuestNote(**payload.model_dump())
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


@router.get("/guests/{guest_id}/notes", response_model=List[GuestNoteResponse])
async def list_notes(
    guest_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGMT_ROLES)),
):
    res = await db.execute(
        select(GuestNote)
        .where(GuestNote.guest_id == guest_id, GuestNote.deleted_at.is_(None))
        .order_by(GuestNote.is_pinned.desc(), GuestNote.created_at.desc())
    )
    return list(res.scalars().all())


# ── Communication ──

@router.post(
    "/communications", response_model=CommunicationLogResponse, status_code=status.HTTP_201_CREATED
)
async def create_communication(
    payload: CommunicationLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGMT_ROLES)),
):
    log = CommunicationLog(**payload.model_dump())
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.get("/guests/{guest_id}/communications", response_model=List[CommunicationLogResponse])
async def list_communications(
    guest_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGMT_ROLES)),
):
    res = await db.execute(
        select(CommunicationLog)
        .where(CommunicationLog.guest_id == guest_id, CommunicationLog.deleted_at.is_(None))
        .order_by(CommunicationLog.created_at.desc())
    )
    return list(res.scalars().all())
