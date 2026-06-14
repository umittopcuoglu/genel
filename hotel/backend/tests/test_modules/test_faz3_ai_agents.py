"""TASK-014…017 — Faz 3 AI ajanları testleri (EventIQ, TechCare, ChefIQ, SecureAI)."""
import pytest
from httpx import AsyncClient

from app.core.agents.event_qi import EventIQAgent, EventIQInput
from app.core.agents.tech_care import TechCareAgent, TechCareInput
from app.core.agents.chef_iq import ChefIQAgent, ChefIQInput
from app.core.agents.secure_ai import SecureAIAgent, SecureAIInput, AccessEvent


# ── Birim testleri (LLM gerekmez, mock-first) ──
@pytest.mark.asyncio
async def test_eventiq_conference_setup():
    agent = EventIQAgent()
    out = await agent.execute(EventIQInput(event_type="conference", pax_count=100))
    assert out.setup_type == "classroom"
    assert out.capacity == 120  # %20 tampon
    assert "lunch" in out.catering_items
    assert 0 < out.confidence <= 1


@pytest.mark.asyncio
async def test_eventiq_wedding_banquet():
    agent = EventIQAgent()
    out = await agent.execute(EventIQInput(event_type="wedding", pax_count=200))
    assert out.setup_type == "banquet"
    assert out.venue_suggestion == "Balo Salonu A"


@pytest.mark.asyncio
async def test_techcare_triage_urgent():
    agent = TechCareAgent()
    out = await agent.execute(TechCareInput(description="Odada gaz kaçağı var, acil!"))
    assert out.category == "Safety"
    assert out.priority == "urgent"


@pytest.mark.asyncio
async def test_techcare_triage_plumbing():
    agent = TechCareAgent()
    out = await agent.execute(TechCareInput(description="Banyoda su sızıntısı"))
    assert out.category == "Plumbing"
    assert out.priority == "high"


@pytest.mark.asyncio
async def test_techcare_triage_general_fallback():
    agent = TechCareAgent()
    out = await agent.execute(TechCareInput(description="Belirsiz bir durum"))
    assert out.category == "General"


@pytest.mark.asyncio
async def test_chefiq_weekend_uplift():
    agent = ChefIQAgent()
    out = await agent.execute(ChefIQInput(item_name="Levrek", recent_sales=100, is_weekend=True))
    assert out.forecast_demand == 135  # 100 * 1.35
    assert out.recommended_stock > out.forecast_demand  # emniyet payı


@pytest.mark.asyncio
async def test_secureai_detects_repeated_denials():
    agent = SecureAIAgent()
    events = [AccessEvent(area="Room 305", result="denied", hour=3) for _ in range(4)]
    events.append(AccessEvent(area="Lobby", result="granted", hour=10))
    out = await agent.execute(SecureAIInput(events=events))
    assert out.total_events == 5
    assert len(out.anomalies) == 1
    assert out.anomalies[0].area == "Room 305"
    assert out.anomalies[0].risk == "high"  # gece + 4 deneme


@pytest.mark.asyncio
async def test_secureai_no_anomaly():
    agent = SecureAIAgent()
    events = [AccessEvent(area="Room 101", result="granted", hour=14)]
    out = await agent.execute(SecureAIInput(events=events))
    assert out.anomalies == []


# ── HTTP endpoint testleri (RBAC + zarf) ──
@pytest.mark.asyncio
async def test_eventiq_endpoint(client: AsyncClient, manager_headers: dict):
    resp = await client.post(
        "/api/v1/ai/eventiq/suggest-setup",
        json={"event_type": "gala", "pax_count": 150},
        headers=manager_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["meta"]["agent"] == "event_qi"
    assert body["data"]["setup_type"] == "banquet"


@pytest.mark.asyncio
async def test_techcare_endpoint_rbac(client: AsyncClient, frontdesk_headers: dict):
    """frontdesk techcare çağıramaz → 403."""
    resp = await client.post(
        "/api/v1/ai/techcare/triage",
        json={"description": "elektrik arızası"},
        headers=frontdesk_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_chefiq_endpoint(client: AsyncClient, manager_headers: dict):
    resp = await client.post(
        "/api/v1/ai/chefiq/forecast-demand",
        json={"item_name": "Pizza", "recent_sales": 80, "is_weekend": False},
        headers=manager_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["item_name"] == "Pizza"


@pytest.mark.asyncio
async def test_secureai_endpoint(client: AsyncClient, manager_headers: dict):
    resp = await client.post(
        "/api/v1/ai/secureai/anomaly-scan",
        json={"events": [
            {"area": "Room 200", "result": "denied", "hour": 2},
            {"area": "Room 200", "result": "denied", "hour": 2},
            {"area": "Room 200", "result": "denied", "hour": 3},
        ]},
        headers=manager_headers,
    )
    assert resp.status_code == 200, resp.text
    assert len(resp.json()["data"]["anomalies"]) == 1
