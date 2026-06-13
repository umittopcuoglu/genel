"""TASK-013 — Analitik Dashboard rapor uçları (occupancy/revenue trend + source mix)."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_occupancy_trend_shape(client: AsyncClient, manager_headers: dict):
    resp = await client.get("/api/v1/reports/occupancy-trend", headers=manager_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert len(data) == 7  # son 7 gün
    for pt in data:
        assert "label" in pt and "value" in pt and "secondary" in pt
        assert 0 <= pt["value"] <= 100


@pytest.mark.asyncio
async def test_revenue_trend_shape(client: AsyncClient, manager_headers: dict):
    resp = await client.get("/api/v1/reports/revenue-trend", headers=manager_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert len(data) == 6  # son 6 ay
    assert all("label" in pt and "value" in pt for pt in data)


@pytest.mark.asyncio
async def test_source_mix_with_data(client: AsyncClient, manager_headers: dict, reservation_db):
    """Tek rezervasyon (default source=direct) → %100 Direct."""
    resp = await client.get("/api/v1/reports/source-mix", headers=manager_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert len(data) >= 1
    direct = next((r for r in data if r["label"] == "Direct"), None)
    assert direct is not None
    assert direct["tone"] == "primary"
    assert sum(r["value"] for r in data) == pytest.approx(100.0, abs=0.5)


@pytest.mark.asyncio
async def test_source_mix_empty(client: AsyncClient, manager_headers: dict):
    """Veri yokken boş liste döner (frontend mock'a düşer)."""
    resp = await client.get("/api/v1/reports/source-mix", headers=manager_headers)
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_analytics_requires_role(client: AsyncClient, frontdesk_headers: dict):
    """frontdesk analitik raporlarını çağıramaz → 403."""
    resp = await client.get("/api/v1/reports/occupancy-trend", headers=frontdesk_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_analytics_no_token_401(client: AsyncClient):
    resp = await client.get("/api/v1/reports/revenue-trend")
    assert resp.status_code == 401
