from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.front_office import Guest, Reservation
from app.models.loyalty_account import LoyaltyAccount
from app.models.complaint import Complaint
from app.models.feedback import Feedback


class Guest360Service:
    @staticmethod
    async def get_guest_profile(guest_id: UUID, db: AsyncSession) -> dict:
        """Misafir 360 profili."""
        guest = await db.get(Guest, guest_id)
        if not guest:
            raise ValueError("Guest not found")

        stays = await db.execute(
            select(func.count(Reservation.id))
            .where(Reservation.guest_id == guest_id)
        )
        total_stays = stays.scalar() or 0

        loyalty = await db.execute(
            select(LoyaltyAccount).where(LoyaltyAccount.guest_id == guest_id)
        )
        loyalty_acc = loyalty.scalars().first()

        complaints = await db.execute(
            select(func.count(Complaint.id))
            .where(Complaint.guest_id == guest_id)
        )
        complaint_count = complaints.scalar() or 0

        feedbacks = await db.execute(
            select(func.count(Feedback.id))
            .where(Feedback.guest_id == guest_id)
        )
        feedback_count = feedbacks.scalar() or 0

        return {
            "basic": {
                "id": str(guest.id),
                "name": f"{guest.first_name} {guest.last_name}",
                "email": guest.email,
                "phone": guest.phone,
            },
            "stays": {
                "total_stays": total_stays,
                "total_revenue": 0.0,
                "last_checkout": None,
                "avg_los_days": 3,
            },
            "preferences": [],
            "loyalty": {
                "tier": loyalty_acc.tier if loyalty_acc else "bronze",
                "available_points": loyalty_acc.available_points if loyalty_acc else 0,
            },
            "feedback": {
                "complaint_count": complaint_count,
                "feedback_count": feedback_count,
            },
        }
