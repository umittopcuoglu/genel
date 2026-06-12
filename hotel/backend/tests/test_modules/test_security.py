"""Güvenlik & KVKK testleri."""
import pytest


# ── Access Logs ──

@pytest.mark.asyncio
async def test_log_access_granted(async_client, frontdesk_headers):
    r = await async_client.post(
        "/api/v1/security/access-logs",
        json={"door_code": "ROOM-101", "method": "card", "granted": True},
        headers=frontdesk_headers,
    )
    assert r.status_code == 201
    assert r.json()["granted"] is True


@pytest.mark.asyncio
async def test_list_access_logs_filter(async_client, frontdesk_headers):
    await async_client.post(
        "/api/v1/security/access-logs",
        json={"door_code": "ROOM-102", "method": "pin", "granted": False, "reason": "wrong PIN"},
        headers=frontdesk_headers,
    )
    r = await async_client.get(
        "/api/v1/security/access-logs?door_code=ROOM-102", headers=frontdesk_headers
    )
    assert r.status_code == 200
    assert all(x["door_code"] == "ROOM-102" for x in r.json())


# ── KVKK Consent ──

@pytest.mark.asyncio
async def test_grant_and_list_consent(async_client, manager_headers, guest_db):
    r = await async_client.post(
        "/api/v1/security/kvkk/consents",
        json={"guest_id": str(guest_db.id), "purpose": "marketing", "text_version": "v1.0"},
        headers=manager_headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["granted"] is True
    lst = await async_client.get(
        f"/api/v1/security/kvkk/guests/{guest_db.id}/consents", headers=manager_headers
    )
    assert any(c["purpose"] == "marketing" for c in lst.json())


@pytest.mark.asyncio
async def test_grant_consent_idempotent(async_client, manager_headers, guest_db):
    r1 = await async_client.post(
        "/api/v1/security/kvkk/consents",
        json={"guest_id": str(guest_db.id), "purpose": "operational"},
        headers=manager_headers,
    )
    r2 = await async_client.post(
        "/api/v1/security/kvkk/consents",
        json={"guest_id": str(guest_db.id), "purpose": "operational"},
        headers=manager_headers,
    )
    # Aynı amaç için ikinci grant aynı kaydı döner (yeni kayıt açmaz)
    assert r1.json()["id"] == r2.json()["id"]


@pytest.mark.asyncio
async def test_revoke_consent(async_client, manager_headers, guest_db):
    r = await async_client.post(
        "/api/v1/security/kvkk/consents",
        json={"guest_id": str(guest_db.id), "purpose": "marketing"},
        headers=manager_headers,
    )
    cid = r.json()["id"]
    rev = await async_client.post(
        f"/api/v1/security/kvkk/consents/{cid}/revoke", headers=manager_headers
    )
    assert rev.status_code == 200
    assert rev.json()["granted"] is False
    assert rev.json()["revoked_at"] is not None


# ── Data Subject Requests ──

@pytest.mark.asyncio
async def test_dsr_access_request(async_client, manager_headers, guest_db):
    r = await async_client.post(
        "/api/v1/security/kvkk/requests",
        json={"guest_id": str(guest_db.id), "request_type": "access"},
        headers=manager_headers,
    )
    assert r.status_code == 201
    rid = r.json()["id"]
    f = await async_client.post(
        f"/api/v1/security/kvkk/requests/{rid}/fulfill", headers=manager_headers
    )
    assert f.json()["status"] == "completed"
    assert f.json()["response_payload"]["id"] == str(guest_db.id)


@pytest.mark.asyncio
async def test_dsr_erase_anonymizes_guest(async_client, manager_headers, guest_db):
    r = await async_client.post(
        "/api/v1/security/kvkk/requests",
        json={"guest_id": str(guest_db.id), "request_type": "erase"},
        headers=manager_headers,
    )
    rid = r.json()["id"]
    await async_client.post(
        f"/api/v1/security/kvkk/requests/{rid}/fulfill", headers=manager_headers
    )
    # Guest profili anonimleştirilmiş olmalı
    profile = await async_client.get(
        f"/api/v1/crm/guests/{guest_db.id}/360", headers=manager_headers
    )
    assert "ANON" in profile.json()["full_name"]


@pytest.mark.asyncio
async def test_dsr_invalid_type(async_client, manager_headers, guest_db):
    r = await async_client.post(
        "/api/v1/security/kvkk/requests",
        json={"guest_id": str(guest_db.id), "request_type": "magic"},
        headers=manager_headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_rbac_frontdesk_cannot_grant_consent(async_client, frontdesk_headers, guest_db):
    r = await async_client.post(
        "/api/v1/security/kvkk/consents",
        json={"guest_id": str(guest_db.id), "purpose": "marketing"},
        headers=frontdesk_headers,
    )
    assert r.status_code == 403
