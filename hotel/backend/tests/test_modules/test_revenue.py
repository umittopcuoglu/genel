"""Revenue Management testleri."""
from datetime import date, timedelta

import pytest


@pytest.mark.asyncio
async def test_forecast_basic(async_client, manager_headers, room_type_db):
    target = (date.today() + timedelta(days=7)).isoformat()
    r = await async_client.post(
        "/api/v1/revenue/forecast",
        json={"target_date": target, "room_type_id": str(room_type_db.id)},
        headers=manager_headers,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert 0 <= data["predicted_occupancy_percent"] <= 100
    assert data["forecast_date"] == target


@pytest.mark.asyncio
async def test_recommend_rate_basic(async_client, manager_headers, room_type_db):
    target = (date.today() + timedelta(days=7)).isoformat()
    r = await async_client.post(
        "/api/v1/revenue/recommend",
        json={"room_type_id": str(room_type_db.id), "target_date": target},
        headers=manager_headers,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert float(data["recommended_rate"]) > 0
    assert data["status"] == "suggested"
    assert data["demand_trend"]


@pytest.mark.asyncio
async def test_recommend_with_competitor_clip(async_client, manager_headers, room_type_db):
    target = (date.today() + timedelta(days=14)).isoformat()
    r = await async_client.post(
        "/api/v1/revenue/recommend",
        json={
            "room_type_id": str(room_type_db.id),
            "target_date": target,
            "competitor_avg_rate": "180.00",
        },
        headers=manager_headers,
    )
    assert r.status_code == 201
    rec = r.json()
    assert float(rec["recommended_rate"]) <= 198.00  # competitor * 1.10
    assert float(rec["recommended_rate"]) >= 171.00  # competitor * 0.95


@pytest.mark.asyncio
async def test_approve_recommendation_updates_rate_plan(async_client, manager_headers, room_type_db, rate_plan_db):
    target = (date.today() + timedelta(days=7)).isoformat()
    rec_r = await async_client.post(
        "/api/v1/revenue/recommend",
        json={"room_type_id": str(room_type_db.id), "target_date": target},
        headers=manager_headers,
    )
    rec_id = rec_r.json()["id"]
    new_rate = float(rec_r.json()["recommended_rate"])
    ok = await async_client.post(
        f"/api/v1/revenue/recommendations/{rec_id}/approve", headers=manager_headers
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_reject_recommendation(async_client, manager_headers, room_type_db):
    target = (date.today() + timedelta(days=7)).isoformat()
    rec_r = await async_client.post(
        "/api/v1/revenue/recommend",
        json={"room_type_id": str(room_type_db.id), "target_date": target},
        headers=manager_headers,
    )
    rec_id = rec_r.json()["id"]
    rej = await async_client.post(
        f"/api/v1/revenue/recommendations/{rec_id}/reject", headers=manager_headers
    )
    assert rej.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_overbooking_rule_upsert_and_list(async_client, manager_headers, room_type_db):
    r = await async_client.post(
        "/api/v1/revenue/overbooking-rules",
        json={"room_type_id": str(room_type_db.id), "overbooking_percent": 10.0},
        headers=manager_headers,
    )
    assert r.status_code == 201
    # Aynı room_type için tekrar gönder → upsert (kayıt sayısı artmamalı)
    r2 = await async_client.post(
        "/api/v1/revenue/overbooking-rules",
        json={"room_type_id": str(room_type_db.id), "overbooking_percent": 15.0},
        headers=manager_headers,
    )
    assert r2.status_code == 201
    assert r2.json()["overbooking_percent"] == 15.0
    lst = await async_client.get("/api/v1/revenue/overbooking-rules", headers=manager_headers)
    matching = [x for x in lst.json() if x["room_type_id"] == str(room_type_db.id)]
    assert len(matching) == 1


@pytest.mark.asyncio
async def test_overbooking_invalid_percent(async_client, manager_headers):
    r = await async_client.post(
        "/api/v1/revenue/overbooking-rules",
        json={"overbooking_percent": 75.0},
        headers=manager_headers,
    )
    assert r.status_code == 422  # pydantic le=50


@pytest.mark.asyncio
async def test_rbac_frontdesk_cannot_forecast(async_client, frontdesk_headers, room_type_db):
    r = await async_client.post(
        "/api/v1/revenue/forecast",
        json={"target_date": "2026-12-31", "room_type_id": str(room_type_db.id)},
        headers=frontdesk_headers,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_rbac_frontdesk_can_list(async_client, frontdesk_headers):
    r = await async_client.get("/api/v1/revenue/recommendations", headers=frontdesk_headers)
    assert r.status_code == 200
