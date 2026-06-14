"""TASK-017 — Güvenlik & Erişim Kontrol & KVKK modülü testleri."""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient


# ── Door Locks ──
@pytest.mark.asyncio
async def test_create_door_lock(client: AsyncClient, manager_headers: dict):
    resp = await client.post(
        "/api/v1/security/door-locks",
        json={"name": "Room 101 Lock", "area": "room"},
        headers=manager_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["is_online"] is True


@pytest.mark.asyncio
async def test_list_door_locks(client: AsyncClient, manager_headers: dict):
    await client.post(
        "/api/v1/security/door-locks",
        json={"name": "Main Entrance", "area": "common"},
        headers=manager_headers,
    )
    resp = await client.get("/api/v1/security/door-locks", headers=manager_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ── Key Cards ──
@pytest.mark.asyncio
async def test_issue_and_revoke_card(client: AsyncClient, frontdesk_headers: dict):
    now = datetime.utcnow()
    resp = await client.post(
        "/api/v1/security/key-cards",
        json={
            "card_number": f"CARD-{uuid4().hex[:8]}",
            "owner_type": "guest",
            "owner_name": "John Doe",
            "valid_from": now.isoformat(),
            "valid_until": (now + timedelta(days=3)).isoformat(),
        },
        headers=frontdesk_headers,
    )
    assert resp.status_code == 201, resp.text
    card_id = resp.json()["id"]
    assert resp.json()["status"] == "active"

    revoke = await client.patch(
        f"/api/v1/security/key-cards/{card_id}/revoke", headers=frontdesk_headers
    )
    assert revoke.status_code == 200
    assert revoke.json()["status"] == "revoked"


@pytest.mark.asyncio
async def test_revoke_card_not_found(client: AsyncClient, frontdesk_headers: dict):
    resp = await client.patch(
        f"/api/v1/security/key-cards/{uuid4()}/revoke", headers=frontdesk_headers
    )
    assert resp.status_code == 404


# ── Access Logs ──
@pytest.mark.asyncio
async def test_log_and_filter_access(client: AsyncClient, manager_headers: dict, frontdesk_headers: dict):
    await client.post(
        "/api/v1/security/access-logs",
        json={"area": "room", "card_number": "C1", "person_name": "Guest", "result": "denied"},
        headers=frontdesk_headers,
    )
    resp = await client.get("/api/v1/security/access-logs?result_filter=denied", headers=manager_headers)
    assert resp.status_code == 200
    assert all(log["result"] == "denied" for log in resp.json())


@pytest.mark.asyncio
async def test_access_logs_requires_manager(client: AsyncClient, frontdesk_headers: dict):
    """frontdesk erişim loglarını sorgulayamaz → 403."""
    resp = await client.get("/api/v1/security/access-logs", headers=frontdesk_headers)
    assert resp.status_code == 403


# ── Incidents ──
@pytest.mark.asyncio
async def test_incident_lifecycle(client: AsyncClient, manager_headers: dict):
    create = await client.post(
        "/api/v1/security/incidents",
        json={"title": "Suspicious activity", "incident_type": "unauthorized_access", "severity": "high"},
        headers=manager_headers,
    )
    assert create.status_code == 201, create.text
    incident_id = create.json()["id"]
    assert create.json()["status"] == "open"

    update = await client.patch(
        f"/api/v1/security/incidents/{incident_id}/status",
        json={"status": "resolved"},
        headers=manager_headers,
    )
    assert update.status_code == 200
    assert update.json()["status"] == "resolved"
    assert update.json()["resolved_at"] is not None


@pytest.mark.asyncio
async def test_incident_invalid_status_422(client: AsyncClient, manager_headers: dict):
    create = await client.post(
        "/api/v1/security/incidents",
        json={"title": "Test", "incident_type": "other"},
        headers=manager_headers,
    )
    incident_id = create.json()["id"]
    resp = await client.patch(
        f"/api/v1/security/incidents/{incident_id}/status",
        json={"status": "bogus"},
        headers=manager_headers,
    )
    assert resp.status_code == 422


# ── KVKK Consents ──
@pytest.mark.asyncio
async def test_kvkk_consent_and_withdraw(client: AsyncClient, frontdesk_headers: dict):
    create = await client.post(
        "/api/v1/security/kvkk/consents",
        json={"guest_name": "Jane Doe", "purpose": "marketing"},
        headers=frontdesk_headers,
    )
    assert create.status_code == 201, create.text
    consent_id = create.json()["id"]
    assert create.json()["status"] == "granted"

    withdraw = await client.patch(
        f"/api/v1/security/kvkk/consents/{consent_id}/withdraw", headers=frontdesk_headers
    )
    assert withdraw.status_code == 200
    assert withdraw.json()["status"] == "withdrawn"


# ── KVKK Data Requests ──
@pytest.mark.asyncio
async def test_kvkk_data_request_flow(client: AsyncClient, manager_headers: dict, frontdesk_headers: dict):
    create = await client.post(
        "/api/v1/security/kvkk/data-requests",
        json={"guest_name": "Ali Veli", "request_type": "deletion", "notes": "GDPR erasure"},
        headers=frontdesk_headers,
    )
    assert create.status_code == 201, create.text
    request_id = create.json()["id"]
    assert create.json()["status"] == "pending"

    complete = await client.patch(
        f"/api/v1/security/kvkk/data-requests/{request_id}/complete", headers=manager_headers
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "completed"
    assert complete.json()["completed_at"] is not None


@pytest.mark.asyncio
async def test_security_no_token_401(client: AsyncClient):
    resp = await client.post(
        "/api/v1/security/door-locks",
        json={"name": "X", "area": "room"},
    )
    assert resp.status_code == 401
