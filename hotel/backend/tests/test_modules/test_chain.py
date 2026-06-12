"""TASK-023 Multi-Property / Chain tests."""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def chain_fixture(async_client, manager_headers):
    """Test zinciri oluştur."""
    response = await async_client.post(
        "/api/v1/console/chains",
        json={
            "name": "Test Hotel Group",
            "code": "THG",
            "description": "Test zinciri",
            "website": "https://testgroup.com",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def property_fixture(async_client, manager_headers, chain_fixture):
    """Test mülkü oluştur."""
    response = await async_client.post(
        "/api/v1/console/properties",
        json={
            "chain_id": chain_fixture["id"],
            "name": "Test Hotel Istanbul",
            "code": "TH-IST",
            "city": "Istanbul",
            "country": "Turkey",
            "total_rooms": 120,
            "star_rating": 4,
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    return response.json()


# ── Chain Tests ──

@pytest.mark.asyncio
async def test_create_chain(client: AsyncClient, manager_headers: dict):
    """Yeni zincir oluştur."""
    response = await client.post(
        "/api/v1/console/chains",
        json={"name": "Luxury Hotels", "code": "LUX", "description": "Luxury zinciri"},
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "LUX"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_chain(client: AsyncClient, manager_headers: dict, chain_fixture):
    """Zincir detayını getir."""
    chain_id = chain_fixture["id"]
    response = await client.get(
        f"/api/v1/console/chains/{chain_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == chain_id


@pytest.mark.asyncio
async def test_update_chain(client: AsyncClient, manager_headers: dict, chain_fixture):
    """Zincir bilgilerini güncelle."""
    chain_id = chain_fixture["id"]
    response = await client.patch(
        f"/api/v1/console/chains/{chain_id}",
        json={"name": "Test Hotel Group Updated", "is_active": False},
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Hotel Group Updated"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_list_chains(client: AsyncClient, manager_headers: dict, chain_fixture):
    """Zincirleri listele."""
    response = await client.get(
        "/api/v1/console/chains",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── Property Tests ──

@pytest.mark.asyncio
async def test_create_property(client: AsyncClient, manager_headers: dict, chain_fixture):
    """Yeni mülk oluştur."""
    response = await client.post(
        "/api/v1/console/properties",
        json={
            "chain_id": chain_fixture["id"],
            "name": "Test Hotel Antalya",
            "code": "TH-AYT",
            "city": "Antalya",
            "country": "Turkey",
            "total_rooms": 200,
            "star_rating": 5,
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "TH-AYT"
    assert data["total_rooms"] == 200


@pytest.mark.asyncio
async def test_get_property(client: AsyncClient, manager_headers: dict, property_fixture):
    """Mülk detayını getir."""
    property_id = property_fixture["id"]
    response = await client.get(
        f"/api/v1/console/properties/{property_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == property_id


@pytest.mark.asyncio
async def test_list_properties(client: AsyncClient, manager_headers: dict, property_fixture):
    """Mülkleri listele."""
    response = await client.get(
        "/api/v1/console/properties",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── PropertyUser Tests ──

@pytest.mark.asyncio
async def test_create_property_user(
    client: AsyncClient, manager_headers: dict, property_fixture, user_db
):
    """Mülke kullanıcı ataması yap."""
    property_id = property_fixture["id"]
    response = await client.post(
        "/api/v1/console/property-users",
        json={
            "property_id": property_id,
            "user_id": str(user_db.id),
            "role": "property_manager",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "property_manager"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_property_users(
    client: AsyncClient, manager_headers: dict, property_fixture, user_db
):
    """Mülk kullanıcı atamalarını listele."""
    property_id = property_fixture["id"]

    # Create first
    await client.post(
        "/api/v1/console/property-users",
        json={
            "property_id": property_id,
            "user_id": str(user_db.id),
            "role": "property_frontdesk",
        },
        headers=manager_headers,
    )

    response = await client.get(
        "/api/v1/console/property-users",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── Consolidated Report Tests ──

@pytest.mark.asyncio
async def test_generate_report(client: AsyncClient, manager_headers: dict, chain_fixture):
    """Konsolide rapor oluştur."""
    response = await client.post(
        "/api/v1/console/reports/generate",
        json={
            "chain_id": chain_fixture["id"],
            "report_type": "daily",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["report_type"] == "daily"
    assert data["total_revenue"] is not None


@pytest.mark.asyncio
async def test_list_reports(client: AsyncClient, manager_headers: dict, chain_fixture):
    """Konsolide raporları listele."""
    # Generate first
    await client.post(
        "/api/v1/console/reports/generate",
        json={"chain_id": chain_fixture["id"], "report_type": "monthly"},
        headers=manager_headers,
    )

    response = await client.get(
        "/api/v1/console/reports",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
