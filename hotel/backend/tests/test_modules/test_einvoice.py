"""GİB e-Fatura testleri: oluştur → XML → gönder → durum → iptal."""
import pytest


GIB_PAYLOAD = {
    "integration_type": "gib_einvoice",
    "name": "GİB Test",
    "enabled": True,
    "params": {
        "provider": "foriba",
        "username": "user",
        "password": "pass",
        "vkn": "1234567890",
        "endpoint_url": "https://efatura-test.example.com/ws",
        "environment": "test",
    },
}


@pytest.fixture
async def gib(async_client, superadmin_headers):
    r = await async_client.post("/api/v1/integrations", json=GIB_PAYLOAD, headers=superadmin_headers)
    assert r.status_code == 201
    return r.json()


@pytest.fixture
async def accounting_headers(async_client, db):
    from app.models.user import User
    from app.routers.auth import get_password_hash

    u = User(
        email="acc@test.com",
        hashed_password=get_password_hash("Acc123!"),
        full_name="Acc",
        role="accounting",
        is_active=True,
    )
    db.add(u)
    await db.commit()
    r = await async_client.post(
        "/api/v1/auth/login", json={"email": "acc@test.com", "password": "Acc123!"}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ── Akış ──

@pytest.mark.asyncio
async def test_create_invoice_calculates_kdv(async_client, gib, accounting_headers):
    r = await async_client.post(
        "/api/v1/einvoice",
        json={
            "customer_name": "Test Müşteri",
            "customer_email": "musteri@test.com",
            "customer_tax_id": "12345678901",
            "subtotal": "100.00",
        },
        headers=accounting_headers,
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["einvoice_status"] == "draft"
    assert float(data["kdv_amount"]) == 20.00
    assert float(data["total_amount"]) == 120.00
    assert data["invoice_number"].startswith("GIB")


@pytest.mark.asyncio
async def test_create_without_integration(async_client, accounting_headers):
    r = await async_client.post(
        "/api/v1/einvoice",
        json={"customer_name": "Test", "customer_email": "x@test.com", "subtotal": "50.00"},
        headers=accounting_headers,
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_invalid_tax_id(async_client, gib, accounting_headers):
    r = await async_client.post(
        "/api/v1/einvoice",
        json={
            "customer_name": "Test",
            "customer_email": "x@test.com",
            "customer_tax_id": "ABC123",
            "subtotal": "10",
        },
        headers=accounting_headers,
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_send_to_gib_success(async_client, gib, accounting_headers):
    c = await async_client.post(
        "/api/v1/einvoice",
        json={"customer_name": "OK", "customer_email": "ok@test.com", "subtotal": "200"},
        headers=accounting_headers,
    )
    iid = c.json()["id"]
    s = await async_client.post(f"/api/v1/einvoice/{iid}/send", headers=accounting_headers)
    assert s.status_code == 200
    data = s.json()
    assert data["einvoice_status"] == "sent"
    assert data["gib_response_code"] == "0000"
    assert data["xml_url"].startswith("https://gib.example.com/foriba/")


@pytest.mark.asyncio
async def test_send_to_gib_rejected(async_client, gib, accounting_headers):
    c = await async_client.post(
        "/api/v1/einvoice",
        json={"customer_name": "Rejected Test", "customer_email": "rejected@test.com", "subtotal": "50"},
        headers=accounting_headers,
    )
    iid = c.json()["id"]
    s = await async_client.post(f"/api/v1/einvoice/{iid}/send", headers=accounting_headers)
    assert s.json()["einvoice_status"] == "failed"
    assert s.json()["gib_response_code"] == "9999"


@pytest.mark.asyncio
async def test_status_advances_to_delivered(async_client, gib, accounting_headers):
    c = await async_client.post(
        "/api/v1/einvoice",
        json={"customer_name": "Delivered Test", "customer_email": "d@test.com", "subtotal": "10"},
        headers=accounting_headers,
    )
    iid = c.json()["id"]
    await async_client.post(f"/api/v1/einvoice/{iid}/send", headers=accounting_headers)
    st = await async_client.get(f"/api/v1/einvoice/{iid}/status", headers=accounting_headers)
    assert st.json()["einvoice_status"] == "delivered"


@pytest.mark.asyncio
async def test_cancel_draft(async_client, gib, accounting_headers):
    c = await async_client.post(
        "/api/v1/einvoice",
        json={"customer_name": "Cancel", "customer_email": "c@test.com", "subtotal": "10"},
        headers=accounting_headers,
    )
    iid = c.json()["id"]
    can = await async_client.post(f"/api/v1/einvoice/{iid}/cancel", headers=accounting_headers)
    assert can.json()["einvoice_status"] == "cancelled"


@pytest.mark.asyncio
async def test_xml_contains_ubl_skeleton(async_client, gib, accounting_headers):
    c = await async_client.post(
        "/api/v1/einvoice",
        json={"customer_name": "Xml", "customer_email": "xml@test.com", "subtotal": "10"},
        headers=accounting_headers,
    )
    iid = c.json()["id"]
    xml = await async_client.get(f"/api/v1/einvoice/{iid}/xml", headers=accounting_headers)
    body = xml.json()["xml"]
    assert "UBLVersionID" in body
    assert "TR1.2" in body
    assert "TEMELFATURA" in body


@pytest.mark.asyncio
async def test_rbac_frontdesk_denied(async_client, gib, frontdesk_headers):
    r = await async_client.post(
        "/api/v1/einvoice",
        json={"customer_name": "Test", "customer_email": "x@test.com", "subtotal": "10"},
        headers=frontdesk_headers,
    )
    assert r.status_code == 403
