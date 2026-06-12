"""TASK-020 IoT / Smart Room tests."""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def iot_device_fixture(async_client, manager_headers, room_db):
    """Test IoT cihazı oluştur."""
    response = await async_client.post(
        "/api/v1/iot/devices",
        json={
            "room_id": str(room_db.id),
            "device_type": "thermostat",
            "name": "Nest Test Termostat",
            "vendor": "google",
            "model": "Nest Learning 3rd Gen",
            "serial_number": "NEST-TEST-001",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def iot_scenario_fixture(async_client, manager_headers):
    """Test IoT senaryosu oluştur."""
    response = await async_client.post(
        "/api/v1/iot/scenarios",
        json={
            "name": "Good Morning",
            "trigger_type": "time_schedule",
            "trigger_config": {"time": "07:00", "days": ["mon", "tue", "wed", "thu", "fri"]},
            "actions": [
                {"device_type": "curtain", "command": "open", "value": 100},
                {"device_type": "light", "command": "set_brightness", "value": 50},
            ],
            "priority": 10,
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    return response.json()


# ── Device Tests ──

@pytest.mark.asyncio
async def test_create_device(client: AsyncClient, manager_headers: dict, room_db):
    """Yeni IoT cihazı oluştur."""
    response = await client.post(
        "/api/v1/iot/devices",
        json={
            "room_id": str(room_db.id),
            "device_type": "light",
            "name": "Philips Hue Test",
            "vendor": "philips",
            "model": "Hue White",
            "serial_number": "HUE-TEST-001",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["device_type"] == "light"
    assert data["status"] == "online"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_device(client: AsyncClient, manager_headers: dict, iot_device_fixture):
    """Cihaz detayını getir."""
    device_id = iot_device_fixture["id"]
    response = await client.get(
        f"/api/v1/iot/devices/{device_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == device_id


@pytest.mark.asyncio
async def test_update_device(client: AsyncClient, manager_headers: dict, iot_device_fixture):
    """Cihaz bilgilerini güncelle."""
    device_id = iot_device_fixture["id"]
    response = await client.patch(
        f"/api/v1/iot/devices/{device_id}",
        json={"name": "Updated Nest Thermostat", "status": "maintenance"},
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Nest Thermostat"
    assert data["status"] == "maintenance"


@pytest.mark.asyncio
async def test_list_devices(client: AsyncClient, manager_headers: dict, iot_device_fixture):
    """Cihazları listele."""
    response = await client.get(
        "/api/v1/iot/devices",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_send_command(client: AsyncClient, manager_headers: dict, iot_device_fixture):
    """Cihaza komut gönder."""
    device_id = iot_device_fixture["id"]
    response = await client.post(
        f"/api/v1/iot/devices/{device_id}/command",
        json={
            "command": "set_temperature",
            "value": {"temperature": 23},
        },
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == device_id


@pytest.mark.asyncio
async def test_get_device_logs(client: AsyncClient, manager_headers: dict, iot_device_fixture):
    """Cihaz loglarını getir."""
    device_id = iot_device_fixture["id"]

    # Send command to generate a log
    await client.post(
        f"/api/v1/iot/devices/{device_id}/command",
        json={"command": "turn_off"},
        headers=manager_headers,
    )

    response = await client.get(
        f"/api/v1/iot/devices/{device_id}/logs",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


# ── Scenario Tests ──

@pytest.mark.asyncio
async def test_create_scenario(client: AsyncClient, manager_headers: dict):
    """Yeni senaryo oluştur."""
    response = await client.post(
        "/api/v1/iot/scenarios",
        json={
            "name": "Good Night",
            "trigger_type": "time_schedule",
            "trigger_config": {"time": "23:00"},
            "actions": [
                {"device_type": "light", "command": "turn_off"},
                {"device_type": "curtain", "command": "close"},
            ],
            "priority": 5,
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Good Night"
    assert data["trigger_type"] == "time_schedule"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_scenario(client: AsyncClient, manager_headers: dict, iot_scenario_fixture):
    """Senaryo detayını getir."""
    scenario_id = iot_scenario_fixture["id"]
    response = await client.get(
        f"/api/v1/iot/scenarios/{scenario_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == scenario_id


@pytest.mark.asyncio
async def test_update_scenario(client: AsyncClient, manager_headers: dict, iot_scenario_fixture):
    """Senaryoyu güncelle."""
    scenario_id = iot_scenario_fixture["id"]
    response = await client.patch(
        f"/api/v1/iot/scenarios/{scenario_id}",
        json={"is_active": False},
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_list_scenarios(client: AsyncClient, manager_headers: dict, iot_scenario_fixture):
    """Senaryoları listele."""
    response = await client.get(
        "/api/v1/iot/scenarios",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_trigger_scenario(client: AsyncClient, manager_headers: dict, iot_scenario_fixture):
    """Senaryoyu manuel tetikle."""
    scenario_id = iot_scenario_fixture["id"]
    response = await client.post(
        f"/api/v1/iot/scenarios/{scenario_id}/trigger",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_id"] == scenario_id
    assert data["actions_executed"] > 0


# ── Energy Tests ──

@pytest.mark.asyncio
async def test_record_energy(client: AsyncClient, manager_headers: dict, room_db):
    """Enerji tüketim kaydı."""
    response = await client.post(
        "/api/v1/iot/energy",
        json={
            "room_id": str(room_db.id),
            "reading_type": "electricity",
            "value": 1.5,
            "unit": "kWh",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["reading_type"] == "electricity"
    assert data["value"] == "1.500"


@pytest.mark.asyncio
async def test_list_energy_readings(client: AsyncClient, manager_headers: dict, room_db):
    """Enerji tüketim kayıtlarını listele."""
    response = await client.get(
        "/api/v1/iot/energy",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── Alert Tests ──

@pytest.mark.asyncio
async def test_list_alerts(client: AsyncClient, manager_headers: dict):
    """Alert'leri listele."""
    response = await client.get(
        "/api/v1/iot/alerts",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
