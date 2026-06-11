from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.loyalty_account import LoyaltyAccount
from app.models.loyalty_transaction import LoyaltyTransaction


class LoyaltyService:
    POINT_MULTIPLIERS = {
        "bronze": 1.0,
        "silver": 1.05,
        "gold": 1.10,
        "platinum": 1.25,
    }

    @staticmethod
    async def earn_points(
        guest_id: UUID, amount: Decimal, folio_id: UUID, db: AsyncSession
    ) -> dict:
        result = await db.execute(
            select(LoyaltyAccount).where(LoyaltyAccount.guest_id == guest_id)
        )
        loyalty = result.scalars().first()

        if not loyalty:
            loyalty = LoyaltyAccount(
                guest_id=guest_id,
                tier="bronze",
                tier_since="2026-06-11",
                total_points=0,
                available_points=0,
                created_by=UUID(int=0),
            )
            db.add(loyalty)
            await db.flush()

        base_points = int(amount)
        multiplier = LoyaltyService.POINT_MULTIPLIERS.get(loyalty.tier, 1.0)
        total_points = int(base_points * multiplier)

        transaction = LoyaltyTransaction(
            loyalty_account_id=loyalty.id,
            transaction_type="earn",
            amount=total_points,
            source_type="folio",
            source_id=folio_id,
            description=f"Folio earnings: {total_points} points",
            balance_before=loyalty.available_points,
            balance_after=loyalty.available_points + total_points,
            created_by=UUID(int=0),
        )

        loyalty.available_points += total_points
        loyalty.total_points += total_points
        loyalty.lifetime_revenue += amount

        db.add(transaction)
        await db.commit()

        return {"points_earned": total_points, "new_balance": loyalty.available_points}

    @staticmethod
    async def redeem_points(
        guest_id: UUID, points: int, redemption_type: str, db: AsyncSession
    ) -> dict:
        result = await db.execute(
            select(LoyaltyAccount).where(LoyaltyAccount.guest_id == guest_id)
        )
        loyalty = result.scalars().first()

        if not loyalty or loyalty.available_points < points:
            raise ValueError("Insufficient loyalty points")

        point_value = {
            "discount": 0.1,
            "free_night": 500,
            "upgrade": 250,
        }
        value = points * point_value.get(redemption_type, 0.1)

        transaction = LoyaltyTransaction(
            loyalty_account_id=loyalty.id,
            transaction_type="redeem",
            amount=-points,
            source_type="manual",
            description=f"{redemption_type}: {points} points redeemed",
            balance_before=loyalty.available_points,
            balance_after=loyalty.available_points - points,
            created_by=UUID(int=0),
        )

        loyalty.available_points -= points
        db.add(transaction)
        await db.commit()

        return {
            "redeemed_points": points,
            "value": value,
            "new_balance": loyalty.available_points,
        }
