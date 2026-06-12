"""Entegrasyon Ayarları modülü testleri: CRUD, RBAC, maskeleme, bağlantı testi."""
import pytest
from httpx import AsyncClient

from app.core.security.param_crypto import decrypt_params, encrypt_params, mask_params


IOT_PAYLOAD = {
    "integration_type": "iot",
    "name": "Kat 1 MQTT Broker",
    "enabled": False,
    "params": {"broker_host": "127.0.0.1", "broker_port": 18883, "password": "supersecret123"},
}

GIB_PAYLOAD = {
    "integration_type": "gib_einvoice",
    "name": "GİB Test Ortamı",
    "enabled": False,
    "params": {
        "provider": "foriba",
        "username": "demo",
        "password": "gizliparola",
        "vkn": "1234567890",
        "endpoint_url": "https://efaturatest.example.com/ws",
        "environment": "test",
    },
}


@pytest.fixture
async def iot_integration(async_client, superadmin_headers):
    resp = await async_client.post("/api/v1/integrations", json=IOT_PAYLOAD, headers=superadmin_headers)
    assert resp.status_code == 201
    return resp.json()


# ── Şifreleme birim testleri ──

def test_encrypt_decrypt_roundtrip():
    params = {"api_key": "abc123", "host": "10.0.0.5"}
    token = encrypt_params(params)
    assert token != "" and "abc123" not in token
    assert decrypt_params(token) == params


def test_decrypt_invalid_returns_empty():
    assert decrypt_params("") == {}
    assert decrypt_params("bozuk-token") == {}


def test_mask_params_hides_secrets():
    masked = mask_params({"password": "supersecret123", "host": "1.2.3.4", "api_key": "ab"})
    assert masked["password"].endswith("t123") and masked["password"].startswith("••••")
    assert masked["host"] == "1.2.3.4"
    assert masked["api_key"] == "••••••••"


# ── CRUD + RBAC ──

@pytest.mark.asyncio
async def test_create_integration(client: AsyncClient, superadmin_headers):
    resp = await client.post("/api/v1/integrations", json=GIB_PAYLOAD, headers=superadmin_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["integration_type"] == "gib_einvoice"
    # Hassas alan maskeli dönmeli, düz metin asla dönmemeli
    assert "gizliparola" not in str(body)
    assert body["params"]["password"].startswith("••••")
    assert body["params"]["vkn"] == "1234567890"


@pytest.mark.asyncio
async def test_create_enabled_requires_params(client: AsyncClient, superadmin_headers):
    resp = await client.post(
        "/api/v1/integrations",
        json={"integration_type": "whatsapp", "name": "WA eksik", "enabled": True, "params": {}},
        headers=superadmin_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_rbac_frontdesk_denied(client: AsyncClient, frontdesk_token):
    headers = {"Authorization": f"Bearer {frontdesk_token}"}
    resp = await client.get("/api/v1/integrations", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_and_filter(client: AsyncClient, superadmin_headers, iot_integration):
    resp = await client.get("/api/v1/integrations?integration_type=iot", headers=superadmin_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1 and items[0]["name"] == "Kat 1 MQTT Broker"


@pytest.mark.asyncio
async def test_update_preserves_masked_secret(client: AsyncClient, superadmin_headers, iot_integration):
    sid = iot_integration["id"]
    # Maskeli parolayı geri gönder + portu değiştir → parola korunmalı
    resp = await client.patch(
        f"/api/v1/integrations/{sid}",
        json={"params": {"password": iot_integration["params"]["password"], "broker_port": 1883}, "enabled": True},
        headers=superadmin_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["params"]["broker_port"] == 1883
    assert body["enabled"] is True
    # Parola hâlâ orijinal son 4 karakteriyle maskeli (123 → "t123" değişmedi)
    assert body["params"]["password"].endswith("t123")


@pytest.mark.asyncio
async def test_get_specs(client: AsyncClient, superadmin_headers):
    resp = await client.get("/api/v1/integrations/specs", headers=superadmin_headers)
    assert resp.status_code == 200
    specs = resp.json()
    assert set(specs.keys()) == {"gib_einvoice", "ota_channel", "gds", "whatsapp", "iot", "payment_gateway"}
    assert any(p["key"] == "broker_host" for p in specs["iot"])


@pytest.mark.asyncio
async def test_delete_superadmin_only(client: AsyncClient, superadmin_headers, manager_headers, iot_integration):
    sid = iot_integration["id"]
    resp = await client.delete(f"/api/v1/integrations/{sid}", headers=manager_headers)
    assert resp.status_code == 403
    resp = await client.delete(f"/api/v1/integrations/{sid}", headers=superadmin_headers)
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/integrations/{sid}", headers=superadmin_headers)
    assert resp.status_code == 404


# ── Bağlantı testi ──

@pytest.mark.asyncio
async def test_connection_test_tcp_success(client: AsyncClient, superadmin_headers):
    """Yerel geçici TCP sunucusuna karşı IoT bağlantı testi başarılı olmalı."""
    import asyncio

    server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        payload = dict(IOT_PAYLOAD, params={"broker_host": "127.0.0.1", "broker_port": port})
        resp = await client.post("/api/v1/integrations", json=payload, headers=superadmin_headers)
        sid = resp.json()["id"]
        resp = await client.post(f"/api/v1/integrations/{sid}/test", headers=superadmin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True and "başarılı" in body["message"]
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_connection_test_tcp_failure(client: AsyncClient, superadmin_headers):
    """Kapalı porta IoT bağlantı testi başarısız dönmeli ve sonuç kaydedilmeli."""
    payload = dict(IOT_PAYLOAD, params={"broker_host": "127.0.0.1", "broker_port": 1})
    resp = await client.post("/api/v1/integrations", json=payload, headers=superadmin_headers)
    sid = resp.json()["id"]
    resp = await client.post(f"/api/v1/integrations/{sid}/test", headers=superadmin_headers)
    assert resp.status_code == 200
    assert resp.json()["ok"] is False
    # Sonuç kayda işlendi mi?
    resp = await client.get(f"/api/v1/integrations/{sid}", headers=superadmin_headers)
    assert resp.json()["last_test_ok"] is False


@pytest.mark.asyncio
async def test_connection_test_missing_params(client: AsyncClient, superadmin_headers):
    resp = await client.post(
        "/api/v1/integrations",
        json={"integration_type": "gds", "name": "GDS taslak", "params": {}},
        headers=superadmin_headers,
    )
    sid = resp.json()["id"]
    resp = await client.post(f"/api/v1/integrations/{sid}/test", headers=superadmin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False and "eksik" in body["message"].lower()
