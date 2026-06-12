"""TASK-022 Voice Control tests."""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def voice_integration_fixture(async_client, manager_headers, room_db):
    """Test sesli asistan entegrasyonu oluştur."""
    response = await async_client.post(
        "/api/v1/voice/integrations",
        json={
            "room_id": str(room_db.id),
            "provider": "alexa",
            "device_id": "amzn1.ask.device.MOCK001",
            "device_name": "Echo Dot Test",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    return response.json()


# ── Integration Tests ──

@pytest.mark.asyncio
async def test_create_integration(client: AsyncClient, manager_headers: dict, room_db):
    """Yeni sesli asistan entegrasyonu oluştur."""
    response = await client.post(
        "/api/v1/voice/integrations",
        json={
            "room_id": str(room_db.id),
            "provider": "google_assistant",
            "device_id": "google-hub-MOCK002",
            "device_name": "Google Hub Test",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "google_assistant"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_integration(client: AsyncClient, manager_headers: dict, voice_integration_fixture):
    """Entegrasyon detayını getir."""
    integration_id = voice_integration_fixture["id"]
    response = await client.get(
        f"/api/v1/voice/integrations/{integration_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == integration_id


@pytest.mark.asyncio
async def test_update_integration(client: AsyncClient, manager_headers: dict, voice_integration_fixture):
    """Entegrasyon bilgilerini güncelle."""
    integration_id = voice_integration_fixture["id"]
    response = await client.patch(
        f"/api/v1/voice/integrations/{integration_id}",
        json={"is_active": False, "locale": "en-US"},
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    assert data["locale"] == "en-US"


@pytest.mark.asyncio
async def test_list_integrations(client: AsyncClient, manager_headers: dict, voice_integration_fixture):
    """Entegrasyonları listele."""
    response = await client.get(
        "/api/v1/voice/integrations",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── Webhook Tests ──

@pytest.mark.asyncio
async def test_alexa_webhook_launch(client: AsyncClient, manager_headers: dict):
    """Alexa launch request webhook."""
    response = await client.post(
        "/api/v1/voice/webhook/alexa",
        json={
            "version": "1.0",
            "session": {"sessionId": "session_001", "user": {"userId": "user_mock"}},
            "request": {"type": "LaunchRequest"},
        },
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["response"]["shouldEndSession"] is False


@pytest.mark.asyncio
async def test_alexa_webhook_intent(client: AsyncClient, manager_headers: dict):
    """Alexa intent request webhook."""
    response = await client.post(
        "/api/v1/voice/webhook/alexa",
        json={
            "version": "1.0",
            "session": {"sessionId": "session_002", "user": {"userId": "user_mock"}},
            "request": {
                "type": "IntentRequest",
                "intent": {"name": "TurnOnLight", "slots": {}},
            },
        },
        headers=manager_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_google_webhook(client: AsyncClient, manager_headers: dict):
    """Google webhook test."""
    response = await client.post(
        "/api/v1/voice/webhook/google",
        json={
            "user": {"userId": "user_mock"},
            "conversation": {"conversationId": "conv_001"},
            "inputs": [{"intent": "set_temperature", "rawInputs": [{"query": "sıcaklığı 22 derece yap"}]}],
        },
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert "payload" in response.json()


# ── Intent Mapping Tests ──

@pytest.mark.asyncio
async def test_create_intent_mapping(client: AsyncClient, manager_headers: dict):
    """Yeni intent eşleştirmesi oluştur."""
    response = await client.post(
        "/api/v1/voice/intents",
        json={
            "provider": "alexa",
            "intent_name": "SetTemperature",
            "action": "set_temperature",
            "description": "Sıcaklık ayarlama komutu",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["intent_name"] == "SetTemperature"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_intent_mappings(client: AsyncClient, manager_headers: dict):
    """Intent eşleştirmelerini listele."""
    response = await client.get(
        "/api/v1/voice/intents",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── Command/Session/Interaction Log Tests ──

@pytest.mark.asyncio
async def test_list_commands(client: AsyncClient, manager_headers: dict):
    """Sesli komut loglarını listele."""
    response = await client.get(
        "/api/v1/voice/commands",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_sessions(client: AsyncClient, manager_headers: dict):
    """Sesli oturumları listele."""
    response = await client.get(
        "/api/v1/voice/sessions",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_interactions(client: AsyncClient, manager_headers: dict):
    """Webhook etkileşimlerini listele."""
    response = await client.get(
        "/api/v1/voice/interactions",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
