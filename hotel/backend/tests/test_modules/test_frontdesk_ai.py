"""FrontDesk AI (temel) — check-in asistanı testleri (birim + HTTP endpoint)."""
import pytest
from httpx import AsyncClient

from app.core.agents.frontdesk_ai import FrontDeskAIAgent, FrontDeskInput


# ── Birim testleri (mock-first, deterministik) ──
@pytest.mark.asyncio
async def test_frontdesk_vip_priority_and_free_upgrade():
    agent = FrontDeskAIAgent()
    out = await agent.execute(FrontDeskInput(
        guest_name="Ayşe Yılmaz", is_vip=True,
        requested_room_type="deluxe", available_upgrade="suite",
    ))
    assert out.priority == "vip"
    assert "ücretsiz" in out.room_recommendation.lower()
    assert "Ayşe Yılmaz" in out.greeting


@pytest.mark.asyncio
async def test_frontdesk_gold_high_priority_discounted_upgrade():
    agent = FrontDeskAIAgent()
    out = await agent.execute(FrontDeskInput(
        guest_name="Mehmet Demir", loyalty_tier="gold",
        requested_room_type="standard", available_upgrade="deluxe",
    ))
    assert out.priority == "high"
    assert "indirimli" in out.room_recommendation.lower()
    # Gold → geç check-out upsell'i + standart oda → kahvaltı upsell'i
    assert any("check-out" in s.lower() for s in out.upsell_suggestions)
    assert any("kahvaltı" in s.lower() for s in out.upsell_suggestions)


@pytest.mark.asyncio
async def test_frontdesk_normal_guest_no_upgrade():
    agent = FrontDeskAIAgent()
    out = await agent.execute(FrontDeskInput(
        guest_name="Can Öz", requested_room_type="standard",
    ))
    assert out.priority == "normal"
    assert "standard" in out.room_recommendation.lower()


@pytest.mark.asyncio
async def test_frontdesk_long_stay_upsell_and_special_requests():
    agent = FrontDeskAIAgent()
    out = await agent.execute(FrontDeskInput(
        guest_name="Elif Kaya", nights=5, requested_room_type="deluxe",
        special_requests=["yüksek kat", "alerjik yastık"],
    ))
    # 5 gece → spa + havalimanı transferi
    assert any("spa" in s.lower() for s in out.upsell_suggestions)
    assert any("transfer" in s.lower() for s in out.upsell_suggestions)
    assert any("yüksek kat" in n for n in out.notes)


# ── HTTP endpoint testleri ──
@pytest.mark.asyncio
async def test_frontdesk_endpoint(client: AsyncClient, frontdesk_headers: dict):
    resp = await client.post(
        "/api/v1/ai/frontdesk/checkin-assist",
        json={"guest_name": "Deniz Ak", "loyalty_tier": "platinum",
              "requested_room_type": "deluxe", "available_upgrade": "suite"},
        headers=frontdesk_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["meta"]["agent"] == "frontdesk_ai"
    assert body["data"]["priority"] == "vip"


@pytest.mark.asyncio
async def test_frontdesk_endpoint_rbac(client: AsyncClient, fb_headers: dict):
    """fb (F&B) rolü front desk asistanını çağıramaz → 403."""
    resp = await client.post(
        "/api/v1/ai/frontdesk/checkin-assist",
        json={"guest_name": "X"},
        headers=fb_headers,
    )
    assert resp.status_code == 403
