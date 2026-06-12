"""TASK-021 Computer Vision tests."""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def cv_model_fixture(async_client, manager_headers):
    """Test CV modeli oluştur."""
    response = await async_client.post(
        "/api/v1/cv/models",
        json={
            "name": "YOLOv8 Room Inspector",
            "version": "1.0.0",
            "model_type": "inspection",
            "framework": "yolov8",
            "accuracy": 95.50,
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def cv_inspection_fixture(async_client, manager_headers, room_db):
    """Test denetimi oluştur."""
    response = await async_client.post(
        "/api/v1/cv/inspections",
        json={
            "room_id": str(room_db.id),
            "inspection_type": "daily",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    return response.json()


# ── CV Model Tests ──

@pytest.mark.asyncio
async def test_create_cv_model(client: AsyncClient, manager_headers: dict):
    """Yeni CV modeli oluştur."""
    response = await client.post(
        "/api/v1/cv/models",
        json={
            "name": "Defect Classifier",
            "version": "2.1.0",
            "model_type": "defect_classification",
            "framework": "pytorch",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Defect Classifier"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_cv_models(client: AsyncClient, manager_headers: dict, cv_model_fixture):
    """CV modellerini listele."""
    response = await client.get(
        "/api/v1/cv/models",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


# ── Inspection Tests ──

@pytest.mark.asyncio
async def test_create_inspection(client: AsyncClient, manager_headers: dict, room_db):
    """Yeni denetim başlat."""
    response = await client.post(
        "/api/v1/cv/inspections",
        json={
            "room_id": str(room_db.id),
            "inspection_type": "deep_clean",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["inspection_type"] == "deep_clean"


@pytest.mark.asyncio
async def test_get_inspection(client: AsyncClient, manager_headers: dict, cv_inspection_fixture):
    """Denetim detayını getir."""
    insp_id = cv_inspection_fixture["id"]
    response = await client.get(
        f"/api/v1/cv/inspections/{insp_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == insp_id


@pytest.mark.asyncio
async def test_list_inspections(client: AsyncClient, manager_headers: dict, cv_inspection_fixture):
    """Denetimleri listele."""
    response = await client.get(
        "/api/v1/cv/inspections",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_run_inspection(client: AsyncClient, manager_headers: dict, cv_inspection_fixture):
    """CV analizini çalıştır."""
    insp_id = cv_inspection_fixture["id"]
    response = await client.post(
        f"/api/v1/cv/inspections/{insp_id}/run",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "score" in data
    assert "defects" in data
    assert "inventory" in data


@pytest.mark.asyncio
async def test_list_defects(client: AsyncClient, manager_headers: dict, cv_inspection_fixture):
    """Denetim kusurlarını listele (önceden run edilmeli)."""
    insp_id = cv_inspection_fixture["id"]
    await client.post(f"/api/v1/cv/inspections/{insp_id}/run", headers=manager_headers)
    response = await client.get(
        f"/api/v1/cv/inspections/{insp_id}/defects",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_verify_defect(client: AsyncClient, manager_headers: dict, cv_inspection_fixture):
    """Kusuru doğrula."""
    insp_id = cv_inspection_fixture["id"]
    run_resp = await client.post(f"/api/v1/cv/inspections/{insp_id}/run", headers=manager_headers)
    defects = run_resp.json().get("defects", [])
    if defects:
        defect_id = defects[0]["id"]
        response = await client.post(
            f"/api/v1/cv/defects/{defect_id}/verify",
            json={"is_verified": True},
            headers=manager_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_verified"] is True


@pytest.mark.asyncio
async def test_list_inventory(client: AsyncClient, manager_headers: dict, cv_inspection_fixture):
    """Envanter listele."""
    insp_id = cv_inspection_fixture["id"]
    await client.post(f"/api/v1/cv/inspections/{insp_id}/run", headers=manager_headers)
    response = await client.get(
        f"/api/v1/cv/inspections/{insp_id}/inventory",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
