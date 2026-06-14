"""WhatsApp testleri: send, webhook verify, inbound bot reply, signature."""
import json
import hmac
import hashlib

import pytest


WA_INTEGRATION = {
    "integration_type": "whatsapp",
    "name": "WhatsApp Test",
    "enabled": True,
    "params": {
        "access_token": "test-token",
        "phone_number_id": "1234567890",
        "webhook_secret": "supersecret",
        "verify_token": "verify-me",
    },
}


@pytest.fixture
async def wa_integration(async_client, superadmin_headers):
    r = await async_client.post(
        "/api/v1/integrations", json=WA_INTEGRATION, headers=superadmin_headers
    )
    assert r.status_code == 201, r.text
    return r.json()


# ── Send ──

@pytest.mark.asyncio
async def test_send_message_mock(async_client, wa_integration, guest_db, frontdesk_headers):
    r = await async_client.post(
        "/api/v1/whatsapp/send",
        json={"to_phone": guest_db.phone, "text": "Hoşgeldiniz", "guest_id": str(guest_db.id)},
        headers=frontdesk_headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["success"] is True
    assert body["external_ref"].startswith("WAMID-MOCK-")


@pytest.mark.asyncio
async def test_send_without_integration_fails(async_client, guest_db, frontdesk_headers):
    r = await async_client.post(
        "/api/v1/whatsapp/send",
        json={"to_phone": "+905550001111", "text": "x"},
        headers=frontdesk_headers,
    )
    assert r.status_code == 400


# ── Webhook verify ──

@pytest.mark.asyncio
async def test_webhook_verify_success(async_client, wa_integration):
    r = await async_client.get(
        "/api/v1/whatsapp/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "verify-me", "hub.challenge": "9999"},
    )
    assert r.status_code == 200
    assert r.json() == 9999


@pytest.mark.asyncio
async def test_webhook_verify_fail_wrong_token(async_client, wa_integration):
    r = await async_client.get(
        "/api/v1/whatsapp/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "9999"},
    )
    assert r.status_code == 403


# ── Webhook inbound + bot reply ──

@pytest.mark.asyncio
async def test_inbound_message_triggers_bot_reply(async_client, wa_integration, guest_db):
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {"from": guest_db.phone, "text": {"body": "Merhaba"}, "id": "wamid.test1"}
                            ]
                        }
                    }
                ]
            }
        ]
    }
    body = json.dumps(payload).encode()
    sig = hmac.new(b"supersecret", body, hashlib.sha256).hexdigest()
    r = await async_client.post(
        "/api/v1/whatsapp/webhook",
        content=body,
        headers={"X-Hub-Signature-256": f"sha256={sig}", "Content-Type": "application/json"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["processed"] == 1
    res = data["results"][0]
    assert res["matched_guest"] == str(guest_db.id)
    assert "Merhaba" in (res["auto_reply"] or "") or "hoş" in (res["auto_reply"] or "").lower()


@pytest.mark.asyncio
async def test_inbound_unknown_phone(async_client, wa_integration):
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [{"from": "+9059999999999", "text": {"body": "hello"}, "id": "x"}]
                        }
                    }
                ]
            }
        ]
    }
    body = json.dumps(payload).encode()
    sig = hmac.new(b"supersecret", body, hashlib.sha256).hexdigest()
    r = await async_client.post(
        "/api/v1/whatsapp/webhook",
        content=body,
        headers={"X-Hub-Signature-256": f"sha256={sig}"},
    )
    assert r.status_code == 200
    assert r.json()["results"][0]["matched_guest"] is None


@pytest.mark.asyncio
async def test_inbound_invalid_signature(async_client, wa_integration):
    payload = {"entry": []}
    body = json.dumps(payload).encode()
    r = await async_client.post(
        "/api/v1/whatsapp/webhook",
        content=body,
        headers={"X-Hub-Signature-256": "sha256=bozuk"},
    )
    assert r.status_code == 403


# ── Bot kuralları (unit) ──

def test_bot_reply_keywords():
    from app.services.whatsapp_service import WhatsAppService as S

    assert "hoş" in (S._bot_reply("Merhaba") or "").lower()
    assert "wi-fi" in (S._bot_reply("Wifi şifresi nedir?") or "").lower() or "wifi" in (S._bot_reply("Wifi şifresi nedir?") or "").lower()
    assert S._bot_reply("rezervasyon yapmak istiyorum") is None  # eşleşmeyen → insana devret


# ── İletişim geçmişine yansıma ──

@pytest.mark.asyncio
async def test_communication_log_recorded(async_client, wa_integration, guest_db, frontdesk_headers):
    await async_client.post(
        "/api/v1/whatsapp/send",
        json={"to_phone": guest_db.phone, "text": "Test mesajı", "guest_id": str(guest_db.id)},
        headers=frontdesk_headers,
    )
    r = await async_client.get(
        f"/api/v1/crm/guests/{guest_db.id}/communications", headers=frontdesk_headers
    )
    assert r.status_code == 200
    items = r.json()
    assert any(x["channel"] == "whatsapp" and x["direction"] == "outbound" for x in items)
