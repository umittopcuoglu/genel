"""InsightAI testleri."""
import pytest


@pytest.mark.asyncio
async def test_summary_default_range(async_client, manager_headers):
    r = await async_client.get("/api/v1/insights/summary", headers=manager_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "total_revenue" in data
    assert "adr" in data
    assert "revpar" in data
    assert "occupancy_percent" in data
    assert 0 <= data["occupancy_percent"] <= 100


@pytest.mark.asyncio
async def test_summary_custom_range(async_client, manager_headers):
    r = await async_client.get(
        "/api/v1/insights/summary?date_from=2026-01-01&date_to=2026-12-31",
        headers=manager_headers,
    )
    assert r.status_code == 200
    assert r.json()["date_from"] == "2026-01-01"


@pytest.mark.asyncio
async def test_channel_mix_empty(async_client, manager_headers):
    r = await async_client.get("/api/v1/insights/channel-mix", headers=manager_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_actions_returns_insights(async_client, manager_headers):
    """Test ortamında doluluk 0 olduğu için 'düşük doluluk' uyarısı çıkmalı."""
    r = await async_client.get("/api/v1/insights/actions", headers=manager_headers)
    assert r.status_code == 200
    actions = r.json()
    assert isinstance(actions, list)
    # En azından düşük doluluk uyarısı bekleniyor (rezervasyon yok)
    titles = [a["title"] for a in actions]
    assert any("doluluk" in t.lower() for t in titles)


@pytest.mark.asyncio
async def test_rbac_frontdesk_denied(async_client, frontdesk_headers):
    r = await async_client.get("/api/v1/insights/summary", headers=frontdesk_headers)
    assert r.status_code == 403
