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


# ── Faz 3 AI ajanları (TASK-014…017) — registry üzerinden ──
from app.core.agents.registry import registry
from app.core.agents.event_qi import EventIQAgent, EventIQInput
from app.core.agents.tech_care import TechCareAgent, TechCareInput
from app.core.agents.chef_iq import ChefIQAgent, ChefIQInput
from app.core.agents.secure_ai import SecureAIAgent, SecureAIInput
from app.core.agents.frontdesk_ai import FrontDeskAIAgent, FrontDeskInput


def _get_agent(name: str, fallback_cls):
    """Registry'den ajanı al; startup lifespan çalışmadıysa (örn. testler) örnekle."""
    agent = registry.get(name)
    if agent is None:
        agent = fallback_cls()
        registry.register(agent)
    return agent


@router.post("/eventiq/suggest-setup")
async def eventiq_suggest_setup(
    req: EventIQInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """EventIQ AI: etkinlik tipi + pax → salon/kurulum/catering önerisi."""
    if current_user.role not in ["superadmin", "manager", "fb"]:
        raise HTTPException(status_code=403)
    agent = _get_agent("event_qi", EventIQAgent)
    output = await agent.execute(req, db=db, user=current_user)
    return {"data": output.model_dump(), "meta": {"agent": "event_qi"}}


@router.post("/techcare/triage")
async def techcare_triage(
    req: TechCareInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """TechCare AI: arıza açıklaması → kategori + öncelik + tahmini süre."""
    if current_user.role not in ["superadmin", "manager", "maintenance"]:
        raise HTTPException(status_code=403)
    agent = _get_agent("tech_care", TechCareAgent)
    output = await agent.execute(req, db=db, user=current_user)
    return {"data": output.model_dump(), "meta": {"agent": "tech_care"}}


@router.post("/chefiq/forecast-demand")
async def chefiq_forecast_demand(
    req: ChefIQInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """ChefIQ AI: geçmiş satış → ürün talep tahmini + önerilen stok."""
    if current_user.role not in ["superadmin", "manager", "fb"]:
        raise HTTPException(status_code=403)
    agent = _get_agent("chef_iq", ChefIQAgent)
    output = await agent.execute(req, db=db, user=current_user)
    return {"data": output.model_dump(), "meta": {"agent": "chef_iq"}}


@router.post("/secureai/anomaly-scan")
async def secureai_anomaly_scan(
    req: SecureAIInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """SecureAI: erişim logları → anomali tespiti + risk skoru."""
    if current_user.role not in ["superadmin", "manager"]:
        raise HTTPException(status_code=403)
    agent = _get_agent("secure_ai", SecureAIAgent)
    output = await agent.execute(req, db=db, user=current_user)
    return {"data": output.model_dump(), "meta": {"agent": "secure_ai"}}


@router.post("/frontdesk/checkin-assist")
async def frontdesk_checkin_assist(
    req: FrontDeskInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """FrontDesk AI: misafir profili → karşılama + oda/upgrade önerisi + upsell + öncelik."""
    if current_user.role not in ["superadmin", "manager", "frontdesk"]:
        raise HTTPException(status_code=403)
    agent = _get_agent("frontdesk_ai", FrontDeskAIAgent)
    output = await agent.execute(req, db=db, user=current_user)
    return {"data": output.model_dump(), "meta": {"agent": "frontdesk_ai"}}
