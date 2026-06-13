"""Payment Gateway testleri: charge / refund / 3DS / RBAC / Luhn."""
import pytest


PAYMENT_INTEGRATION = {
    "integration_type": "payment_gateway",
    "name": "iyzico Test",
    "enabled": True,
    "params": {
        "provider": "iyzico",
        "api_key": "test-key",
        "secret_key": "test-secret",
        "endpoint_url": "https://sandbox-api.iyzipay.com",
        "use_3d_secure": False,
        "currency": "TRY",
    },
}

VALID_CARD = {
    "holder_name": "Test User",
    "number": "4111111111111111",
    "exp_month": 12,
    "exp_year": 2030,
    "cvc": "123",
}

DECLINED_CARD = {**VALID_CARD, "number": "4000000000000002"}
INVALID_LUHN = {**VALID_CARD, "number": "4111111111111112"}


@pytest.fixture
async def payment_integration(async_client, superadmin_headers):
    resp = await async_client.post(
        "/api/v1/integrations", json=PAYMENT_INTEGRATION, headers=superadmin_headers
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Charge ──

@pytest.mark.asyncio
async def test_charge_success(async_client, payment_integration, frontdesk_headers):
    resp = await async_client.post(
        "/api/v1/payments/charge",
        json={"amount": "250.00", "currency": "TRY", "card": VALID_CARD},
        headers=frontdesk_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["txn"]["status"] == "succeeded"
    assert data["txn"]["provider"] == "iyzico"
    assert data["txn"]["card_last4"] == "1111"
    assert data["txn"]["card_brand"] == "VISA"
    assert data["txn"]["provider_ref"].startswith("IYZICO-")


@pytest.mark.asyncio
async def test_charge_declined(async_client, payment_integration, frontdesk_headers):
    resp = await async_client.post(
        "/api/v1/payments/charge",
        json={"amount": "100.00", "currency": "TRY", "card": DECLINED_CARD},
        headers=frontdesk_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is False
    assert data["txn"]["status"] == "failed"
    assert data["txn"]["error_message"] == "card_declined"


@pytest.mark.asyncio
async def test_charge_invalid_luhn(async_client, payment_integration, frontdesk_headers):
    resp = await async_client.post(
        "/api/v1/payments/charge",
        json={"amount": "50.00", "currency": "TRY", "card": INVALID_LUHN},
        headers=frontdesk_headers,
    )
    assert resp.status_code == 400
    body = resp.json()
    msg = body.get("detail") or body.get("error", {}).get("message", "")
    assert "Luhn" in msg


@pytest.mark.asyncio
async def test_charge_no_active_integration(async_client, frontdesk_headers):
    resp = await async_client.post(
        "/api/v1/payments/charge",
        json={"amount": "10.00", "currency": "TRY", "card": VALID_CARD},
        headers=frontdesk_headers,
    )
    assert resp.status_code == 400
    body = resp.json()
    msg = (body.get("detail") or body.get("error", {}).get("message", "")).lower()
    assert "ödeme entegrasyonu" in msg or "entegrasyon" in msg


# ── 3DS akışı ──

@pytest.mark.asyncio
async def test_charge_3ds_redirect_then_complete(async_client, payment_integration, frontdesk_headers):
    resp = await async_client.post(
        "/api/v1/payments/charge",
        json={"amount": "300.00", "currency": "TRY", "card": VALID_CARD, "use_3d_secure": True},
        headers=frontdesk_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["redirect_url"] is not None
    assert data["txn"]["status"] == "pending"
    txn_id = data["txn"]["id"]

    # Bankadan başarı callback'i
    cb = await async_client.get(f"/api/v1/payments/3ds/callback?txn={txn_id}&ok=1")
    assert cb.status_code == 200
    assert cb.json()["status"] == "succeeded"


@pytest.mark.asyncio
async def test_3ds_callback_failure(async_client, payment_integration, frontdesk_headers):
    resp = await async_client.post(
        "/api/v1/payments/charge",
        json={"amount": "300.00", "currency": "TRY", "card": VALID_CARD, "use_3d_secure": True},
        headers=frontdesk_headers,
    )
    txn_id = resp.json()["txn"]["id"]
    cb = await async_client.get(f"/api/v1/payments/3ds/callback?txn={txn_id}&ok=0")
    assert cb.status_code == 200
    assert cb.json()["status"] == "failed"


# ── Refund ──

@pytest.mark.asyncio
async def test_refund_full(async_client, payment_integration, frontdesk_headers):
    ch = await async_client.post(
        "/api/v1/payments/charge",
        json={"amount": "100.00", "currency": "TRY", "card": VALID_CARD},
        headers=frontdesk_headers,
    )
    txn_id = ch.json()["txn"]["id"]
    refund = await async_client.post(
        "/api/v1/payments/refund",
        json={"txn_id": txn_id, "reason": "müşteri iadesi"},
        headers=frontdesk_headers,
    )
    assert refund.status_code == 201
    body = refund.json()
    assert body["kind"] == "refund"
    assert body["status"] == "succeeded"
    assert float(body["amount"]) == 100.00


@pytest.mark.asyncio
async def test_refund_partial(async_client, payment_integration, frontdesk_headers):
    ch = await async_client.post(
        "/api/v1/payments/charge",
        json={"amount": "200.00", "currency": "TRY", "card": VALID_CARD},
        headers=frontdesk_headers,
    )
    txn_id = ch.json()["txn"]["id"]
    refund = await async_client.post(
        "/api/v1/payments/refund",
        json={"txn_id": txn_id, "amount": "50.00"},
        headers=frontdesk_headers,
    )
    assert refund.status_code == 201
    assert float(refund.json()["amount"]) == 50.00


@pytest.mark.asyncio
async def test_refund_over_original(async_client, payment_integration, frontdesk_headers):
    ch = await async_client.post(
        "/api/v1/payments/charge",
        json={"amount": "50.00", "currency": "TRY", "card": VALID_CARD},
        headers=frontdesk_headers,
    )
    txn_id = ch.json()["txn"]["id"]
    refund = await async_client.post(
        "/api/v1/payments/refund",
        json={"txn_id": txn_id, "amount": "100.00"},
        headers=frontdesk_headers,
    )
    assert refund.status_code == 400


@pytest.mark.asyncio
async def test_refund_failed_txn_rejected(async_client, payment_integration, frontdesk_headers):
    ch = await async_client.post(
        "/api/v1/payments/charge",
        json={"amount": "50.00", "currency": "TRY", "card": DECLINED_CARD},
        headers=frontdesk_headers,
    )
    txn_id = ch.json()["txn"]["id"]
    refund = await async_client.post(
        "/api/v1/payments/refund",
        json={"txn_id": txn_id},
        headers=frontdesk_headers,
    )
    assert refund.status_code == 400


# ── Liste + RBAC ──

@pytest.mark.asyncio
async def test_list_transactions(async_client, payment_integration, frontdesk_headers):
    for amt in ("10.00", "20.00"):
        await async_client.post(
            "/api/v1/payments/charge",
            json={"amount": amt, "currency": "TRY", "card": VALID_CARD},
            headers=frontdesk_headers,
        )
    resp = await async_client.get("/api/v1/payments", headers=frontdesk_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_rbac_housekeeping_denied(async_client, payment_integration, housekeeping_token):
    resp = await async_client.post(
        "/api/v1/payments/charge",
        json={"amount": "10.00", "currency": "TRY", "card": VALID_CARD},
        headers={"Authorization": f"Bearer {housekeeping_token}"},
    )
    assert resp.status_code == 403
