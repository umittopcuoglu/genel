"""TASK-015 Maintenance & Technical Service tests."""
import pytest
from uuid import uuid4
from datetime import date, datetime, timedelta
from decimal import Decimal
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_asset(client: AsyncClient, manager_headers: dict):
    """Yeni varlık oluştur."""
    response = await client.post(
        "/api/v1/maintenance/assets",
        json={
            "name": "HVAC Unit - Room 101",
            "category": "HVAC",
            "location": "Room 101",
            "purchase_date": "2023-01-15",
            "warranty_end_date": "2026-01-15",
            "notes": "Central AC system",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "HVAC Unit - Room 101"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_get_asset(client: AsyncClient, manager_headers: dict, assets_fixture):
    """Varlık detaylarını getir."""
    asset_id = assets_fixture["asset_id"]
    response = await client.get(
        f"/api/v1/maintenance/assets/{asset_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(asset_id)
    assert data["category"] == "Electrical"


@pytest.mark.asyncio
async def test_list_assets(client: AsyncClient, manager_headers: dict):
    """Varlıkları listele."""
    response = await client.get(
        "/api/v1/maintenance/assets",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_work_order(client: AsyncClient, manager_headers: dict):
    """Yeni iş emri oluştur."""
    response = await client.post(
        "/api/v1/maintenance/work-orders",
        json={
            "room_id": str(uuid4()),
            "category": "Plumbing",
            "priority": "high",
            "description": "Leaking faucet in bathroom",
            "estimated_hours": 2,
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "Plumbing"
    assert data["priority"] == "high"
    assert data["status"] == "open"


@pytest.mark.asyncio
async def test_get_work_order(client: AsyncClient, manager_headers: dict, work_order_fixture):
    """İş emri detaylarını getir."""
    work_order_id = work_order_fixture["work_order_id"]
    response = await client.get(
        f"/api/v1/maintenance/work-orders/{work_order_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(work_order_id)


@pytest.mark.asyncio
async def test_list_work_orders(client: AsyncClient, manager_headers: dict):
    """İş emirlerini listele."""
    response = await client.get(
        "/api/v1/maintenance/work-orders",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_update_work_order_status(client: AsyncClient, manager_headers: dict, work_order_fixture):
    """İş emri durumunu güncelle."""
    work_order_id = work_order_fixture["work_order_id"]
    response = await client.patch(
        f"/api/v1/maintenance/work-orders/{work_order_id}/status",
        json={"status": "assigned", "notes": "Assigned to John"},
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "assigned"


@pytest.mark.asyncio
async def test_assign_work_order(client: AsyncClient, manager_headers: dict, work_order_fixture):
    """İş emrini personele ata."""
    work_order_id = work_order_fixture["work_order_id"]
    maintenance_user_id = uuid4()

    response = await client.patch(
        f"/api/v1/maintenance/work-orders/{work_order_id}/assign",
        json={"assigned_to": str(maintenance_user_id)},
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "assigned"
    assert data["assigned_to"] == str(maintenance_user_id)


@pytest.mark.asyncio
async def test_create_preventive_maintenance(client: AsyncClient, manager_headers: dict, assets_fixture):
    """Preventif bakım planı oluştur."""
    asset_id = assets_fixture["asset_id"]
    response = await client.post(
        "/api/v1/maintenance/preventive-maintenance",
        json={
            "asset_id": str(asset_id),
            "description": "Quarterly HVAC inspection",
            "frequency_days": 90,
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["frequency_days"] == 90
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_get_due_maintenance(client: AsyncClient, manager_headers: dict):
    """Vadesi gelen bakımları getir."""
    response = await client.get(
        "/api/v1/maintenance/preventive-maintenance/due",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_log_maintenance(client: AsyncClient, manager_headers: dict, work_order_fixture):
    """Bakım işlemini kaydet."""
    work_order_id = work_order_fixture["work_order_id"]
    response = await client.post(
        "/api/v1/maintenance/logs",
        json={
            "work_order_id": str(work_order_id),
            "parts_used": "Faucet cartridge",
            "hours_spent": "1.5",
            "cost": "50.00",
            "notes": "Replaced faulty cartridge",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert float(data["hours_spent"]) == 1.5
    assert float(data["cost"]) == 50.0


@pytest.mark.asyncio
async def test_get_work_order_logs(client: AsyncClient, manager_headers: dict, work_order_fixture):
    """İş emrinin bakım geçmişini getir."""
    work_order_id = work_order_fixture["work_order_id"]

    # Log kaydı ekle
    await client.post(
        "/api/v1/maintenance/logs",
        json={
            "work_order_id": str(work_order_id),
            "parts_used": "Test part",
            "hours_spent": "2.0",
            "cost": "100.00",
        },
        headers=manager_headers,
    )

    response = await client.get(
        f"/api/v1/maintenance/logs/{work_order_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
