"""Revenue Management router'ı: doluluk tahmini, fiyat önerisi, overbooking."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.occupancy_forecast import OccupancyForecast
from app.models.overbooking_rule import OverbookingRule
from app.models.rate_recommendation import RateRecommendation
from app.models.user import User
from app.services.revenue_service import RevenueService

router = APIRouter(prefix="/api/v1/revenue", tags=["Revenue Management"])

MGR_ROLES = ["superadmin", "manager"]
READ_ROLES = ["superadmin", "manager", "frontdesk", "accounting"]


# ── Schemas ──

class ForecastRequest(BaseModel):
    target_date: date
    room_type_id: Optional[UUID] = None
    horizon_days: int = Field(default=30, ge=1, le=365)


class RecommendRequest(BaseModel):
    room_type_id: UUID
    target_date: date
    competitor_avg_rate: Optional[Decimal] = None


class OverbookingRuleRequest(BaseModel):
    room_type_id: Optional[UUID] = None
    channel_id: Optional[UUID] = None
    overbooking_percent: float = Field(ge=0, le=50)
    enabled: bool = True
    note: Optional[str] = None


class ForecastResponse(BaseModel):
    id: UUID
    room_type_id: Optional[UUID]
    forecast_date: str
    predicted_occupancy_percent: float
    predicted_rooms_occupied: int
    confidence_interval: str
    forecast_method: str
    forecast_horizon_days: int

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    id: UUID
    room_type_id: UUID
    date: str
    recommended_rate: Decimal
    current_rate: Decimal
    price_change_percent: float
    rationale: str
    confidence_score: float
    occupancy_forecast: float
    demand_trend: str
    competitor_avg_rate: Optional[Decimal]
    status: str

    class Config:
        from_attributes = True


class OverbookingRuleResponse(BaseModel):
    id: UUID
    room_type_id: Optional[UUID]
    channel_id: Optional[UUID]
    overbooking_percent: float
    enabled: bool
    note: Optional[str]

    class Config:
        from_attributes = True


# ── Endpoints ──

@router.post("/forecast", response_model=ForecastResponse, status_code=status.HTTP_201_CREATED)
async def forecast(
    req: ForecastRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGR_ROLES)),
):
    f = await RevenueService.forecast_occupancy(
        db, req.target_date, room_type_id=req.room_type_id, horizon_days=req.horizon_days
    )
    return ForecastResponse.model_validate(f)


@router.post("/recommend", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED)
async def recommend(
    req: RecommendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGR_ROLES)),
):
    try:
        rec = await RevenueService.recommend_rate(
            db, req.room_type_id, req.target_date, competitor_avg_rate=req.competitor_avg_rate
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return RecommendationResponse.model_validate(rec)


@router.post("/recommendations/{rec_id}/approve", response_model=RecommendationResponse)
async def approve(
    rec_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGR_ROLES)),
):
    try:
        rec = await RevenueService.approve_recommendation(db, rec_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return RecommendationResponse.model_validate(rec)


@router.post("/recommendations/{rec_id}/reject", response_model=RecommendationResponse)
async def reject(
    rec_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGR_ROLES)),
):
    try:
        rec = await RevenueService.reject_recommendation(db, rec_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return RecommendationResponse.model_validate(rec)


@router.get("/recommendations", response_model=List[RecommendationResponse])
async def list_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    res = await db.execute(
        select(RateRecommendation)
        .where(RateRecommendation.deleted_at.is_(None))
        .order_by(RateRecommendation.created_at.desc())
    )
    return [RecommendationResponse.model_validate(r) for r in res.scalars().all()]


@router.post(
    "/overbooking-rules",
    response_model=OverbookingRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_rule(
    req: OverbookingRuleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(MGR_ROLES)),
):
    try:
        rule = await RevenueService.upsert_overbooking_rule(
            db,
            room_type_id=req.room_type_id,
            channel_id=req.channel_id,
            overbooking_percent=req.overbooking_percent,
            enabled=req.enabled,
            note=req.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return OverbookingRuleResponse.model_validate(rule)


@router.get("/overbooking-rules", response_model=List[OverbookingRuleResponse])
async def list_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(READ_ROLES)),
):
    res = await db.execute(
        select(OverbookingRule).where(OverbookingRule.deleted_at.is_(None))
    )
    return [OverbookingRuleResponse.model_validate(r) for r in res.scalars().all()]
