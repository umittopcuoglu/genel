from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.complaint import Complaint


router = APIRouter(prefix="/complaints", tags=["Complaints"])


class ComplaintCreateRequest(BaseModel):
    guest_id: UUID
    reservation_id: UUID
    title: str
    description: str
    complaint_type: str
    severity: str


class ComplaintResponse(BaseModel):
    id: UUID
    title: str
    description: str
    status: str
    severity: str


@router.post("")
async def create_complaint(
    req: ComplaintCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComplaintResponse:
    complaint = Complaint(
        guest_id=req.guest_id,
        reservation_id=req.reservation_id,
        title=req.title,
        description=req.description,
        complaint_type=req.complaint_type,
        severity=req.severity,
        status="open",
        created_by=current_user.id,
    )
    db.add(complaint)
    await db.commit()

    return ComplaintResponse(
        id=complaint.id,
        title=complaint.title,
        description=complaint.description,
        status=complaint.status,
        severity=complaint.severity,
    )


@router.get("")
async def list_complaints(
    status: str | None = None,
    severity: str | None = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ComplaintResponse]:
    if current_user.role not in ["manager", "superadmin"]:
        raise HTTPException(status_code=403)

    query = select(Complaint)
    if status:
        query = query.where(Complaint.status == status)
    if severity:
        query = query.where(Complaint.severity == severity)

    result = await db.execute(query.limit(limit))
    complaints = result.scalars().all()

    return [
        ComplaintResponse(
            id=c.id,
            title=c.title,
            description=c.description,
            status=c.status,
            severity=c.severity,
        )
        for c in complaints
    ]


@router.patch("/{complaint_id}/assign")
async def assign_complaint(
    complaint_id: UUID,
    assigned_to: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComplaintResponse:
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalars().first()
    if not complaint:
        raise HTTPException(status_code=404)

    complaint.assigned_to = assigned_to
    complaint.status = "assigned"
    await db.commit()

    return ComplaintResponse(
        id=complaint.id,
        title=complaint.title,
        description=complaint.description,
        status=complaint.status,
        severity=complaint.severity,
    )
