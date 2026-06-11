from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.feedback import Feedback


router = APIRouter(prefix="/feedback", tags=["Feedback"])


class FeedbackSubmitRequest(BaseModel):
    guest_id: UUID
    reservation_id: UUID
    rating: int
    comment: str
    categories: str


class FeedbackResponse(BaseModel):
    id: UUID
    rating: int
    comment: str
    status: str


@router.post("/submit")
async def submit_feedback(
    req: FeedbackSubmitRequest,
    db: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    if not (1 <= req.rating <= 5):
        raise HTTPException(status_code=422, detail="Rating must be 1-5")

    feedback = Feedback(
        guest_id=req.guest_id,
        reservation_id=req.reservation_id,
        rating=req.rating,
        comment=req.comment,
        categories=req.categories,
        status="new",
        created_by=UUID(int=0),
    )
    db.add(feedback)
    await db.commit()

    return FeedbackResponse(
        id=feedback.id,
        rating=feedback.rating,
        comment=feedback.comment,
        status=feedback.status,
    )


@router.get("")
async def list_feedback(
    status: str | None = None,
    rating_min: int | None = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FeedbackResponse]:
    query = select(Feedback)
    if status:
        query = query.where(Feedback.status == status)
    if rating_min:
        query = query.where(Feedback.rating >= rating_min)

    result = await db.execute(query.limit(limit))
    feedbacks = result.scalars().all()

    return [
        FeedbackResponse(
            id=f.id,
            rating=f.rating,
            comment=f.comment,
            status=f.status,
        )
        for f in feedbacks
    ]


@router.patch("/{feedback_id}/respond")
async def respond_to_feedback(
    feedback_id: UUID,
    manager_response: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    feedback = result.scalars().first()
    if not feedback:
        raise HTTPException(status_code=404)

    feedback.manager_response = manager_response
    feedback.status = "responded"
    await db.commit()

    return FeedbackResponse(
        id=feedback.id,
        rating=feedback.rating,
        comment=feedback.comment,
        status=feedback.status,
    )
