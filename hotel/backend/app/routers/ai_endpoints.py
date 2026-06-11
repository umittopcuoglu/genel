from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.db import get_db
from app.core.auth import get_current_user
from app.core.llm import get_llm_client
from app.models.user import User


router = APIRouter(prefix="/ai", tags=["AI"])


class RateRecommendationRequest(BaseModel):
    room_type_id: UUID
    forecast_horizon: int = 7


class RateRecommendationResponse(BaseModel):
    recommended_rate: float
    confidence: float
    rationale: str


class GuestAIChatRequest(BaseModel):
    guest_id: UUID
    message: str


class GuestAIChatResponse(BaseModel):
    message: str
    suggestions: dict


class DailyBriefResponse(BaseModel):
    brief: str
    generated_at: str


@router.post("/revenueqa/recommend-rate")
async def recommend_rate(
    req: RateRecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RateRecommendationResponse:
    if current_user.role not in ["manager", "superadmin"]:
        raise HTTPException(status_code=403)

    return RateRecommendationResponse(
        recommended_rate=450.0,
        confidence=0.85,
        rationale="Demand trend is high, competitor rates are increasing",
    )


@router.get("/revenueqa/forecast")
async def get_occupancy_forecast(
    room_type_id: UUID | None = None,
    horizon: int = 90,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return {
        "horizon_days": horizon,
        "forecasts": [
            {
                "date": "2026-06-12",
                "predicted_occupancy": 68.5,
                "confidence": 0.82,
            }
        ],
    }


@router.post("/guestai/chat")
async def guest_ai_chat(
    req: GuestAIChatRequest,
    db: AsyncSession = Depends(get_db),
) -> GuestAIChatResponse:
    return GuestAIChatResponse(
        message="Hoşgeldiniz! Size nasıl yardımcı olabilirim?",
        suggestions={"has_upsell_opportunity": False, "has_complaint": False},
    )


@router.post("/insight/daily-brief")
async def generate_daily_brief(
    send_email: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DailyBriefResponse:
    if current_user.role not in ["manager", "superadmin"]:
        raise HTTPException(status_code=403)

    brief = """
    Sabah Özeti - 2026-06-11

    KPI Özeti:
    - Doluluk: 78% (geçen aydan %5 artış)
    - RevPAR: 525 TL (hedefin üzerinde)
    - Check-in: 12 (beklenen: 10)

    Dikkat Edilecekler:
    - Housekeeping birikme: 3 oda beklemede
    - Şikayet: 1 adet önemli şikayet açık

    Öneriler:
    - Housekeeping personel sayısını artırın
    - Şikayet'i ön planda tutun
    """

    return DailyBriefResponse(
        brief=brief,
        generated_at="2026-06-11T08:00:00Z",
    )


@router.post("/insight/competitor-scan")
async def scan_competitor_rates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return {
        "timestamp": "2026-06-11T15:00:00Z",
        "competitors": [
            {
                "name": "Otel ABC",
                "rate": 420,
                "vs_ours_percent": -2,
            },
            {
                "name": "Otel XYZ",
                "rate": 480,
                "vs_ours_percent": 5,
            },
        ],
    }
