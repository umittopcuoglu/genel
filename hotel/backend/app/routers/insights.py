"""InsightAI router'ı: özet KPI'lar, kanal mix, aksiyon önerileri."""
from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.user import User
from app.services.insights_service import InsightsService

router = APIRouter(prefix="/api/v1/insights", tags=["InsightAI"])

VIEW_ROLES = ["superadmin", "manager", "accounting"]


class SummaryResponse(BaseModel):
    date_from: str
    date_to: str
    total_revenue: float
    total_stays: int
    adr: float
    revpar: float
    occupancy_percent: float


class ChannelMixRow(BaseModel):
    channel: str
    count: int
    share_percent: float


class InsightRow(BaseModel):
    severity: str
    title: str
    message: str
    action: str


@router.get("/summary", response_model=SummaryResponse)
async def summary(
    date_from: date = Query(None),
    date_to: date = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(VIEW_ROLES)),
):
    today = date.today()
    df = date_from or (today - timedelta(days=30))
    dt = date_to or today
    return await InsightsService.revenue_summary(db, df, dt)


@router.get("/channel-mix", response_model=List[ChannelMixRow])
async def channel_mix(
    date_from: date = Query(None),
    date_to: date = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(VIEW_ROLES)),
):
    today = date.today()
    df = date_from or (today - timedelta(days=30))
    dt = date_to or today
    return await InsightsService.channel_mix(db, df, dt)


@router.get("/actions", response_model=List[InsightRow])
async def actions(
    date_from: date = Query(None),
    date_to: date = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(VIEW_ROLES)),
):
    today = date.today()
    df = date_from or (today - timedelta(days=30))
    dt = date_to or today
    return await InsightsService.actionable_insights(db, df, dt)
