from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.loyalty_account import LoyaltyAccount
from app.models.loyalty_transaction import LoyaltyTransaction
from app.services.loyalty_service import LoyaltyService


router = APIRouter(prefix="/loyalty", tags=["Loyalty"])


class EarnPointsRequest(BaseModel):
    guest_id: UUID
    amount: float
    folio_id: UUID


class RedeemPointsRequest(BaseModel):
    guest_id: UUID
    points: int
    redemption_type: str


class LoyaltyAccountResponse(BaseModel):
    id: UUID
    tier: str
    available_points: int
    lifetime_stays: int
    lifetime_revenue: float


@router.post("/earn")
async def earn_points(
    req: EarnPointsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await LoyaltyService.earn_points(req.guest_id, req.amount, req.folio_id, db)
    return result


@router.post("/redeem")
async def redeem_points(
    req: RedeemPointsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        result = await LoyaltyService.redeem_points(
            req.guest_id, req.points, req.redemption_type, db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/accounts/{guest_id}")
async def get_loyalty_account(
    guest_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LoyaltyAccountResponse:
    result = await db.execute(
        select(LoyaltyAccount).where(LoyaltyAccount.guest_id == guest_id)
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404)
    return LoyaltyAccountResponse(
        id=account.id,
        tier=account.tier,
        available_points=account.available_points,
        lifetime_stays=account.lifetime_stays,
        lifetime_revenue=float(account.lifetime_revenue),
    )


@router.get("/accounts/{guest_id}/transactions")
async def get_loyalty_transactions(
    guest_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    result = await db.execute(
        select(LoyaltyTransaction)
        .join(LoyaltyAccount)
        .where(LoyaltyAccount.guest_id == guest_id)
        .limit(limit)
    )
    transactions = result.scalars().all()
    return [
        {
            "type": t.transaction_type,
            "amount": t.amount,
            "description": t.description,
            "balance_after": t.balance_after,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in transactions
    ]
