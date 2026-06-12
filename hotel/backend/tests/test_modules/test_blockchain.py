"""TASK-025 Blockchain Identity / SSI tests."""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def blockchain_identity_fixture(async_client, manager_headers, guest_db):
    """Test DID oluştur."""
    response = await async_client.post(
        "/api/v1/blockchain/identities",
        json={"guest_id": str(guest_db.id)},
        headers=manager_headers,
    )
    assert response.status_code == 201
    return response.json()


# ── DID Tests ──

@pytest.mark.asyncio
async def test_create_did(client: AsyncClient, manager_headers: dict, guest_db):
    """Yeni DID oluştur."""
    response = await client.post(
        "/api/v1/blockchain/identities",
        json={"guest_id": str(guest_db.id)},
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["did"].startswith("did:")
    assert data["status"] == "active"
    assert data["chain_tx_hash"] is not None


@pytest.mark.asyncio
async def test_get_identity(client: AsyncClient, manager_headers: dict, blockchain_identity_fixture):
    """DID detayını getir."""
    identity_id = blockchain_identity_fixture["id"]
    response = await client.get(
        f"/api/v1/blockchain/identities/{identity_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == identity_id


@pytest.mark.asyncio
async def test_get_identity_by_guest(client: AsyncClient, manager_headers: dict, blockchain_identity_fixture, guest_db):
    """Misafire göre DID getir."""
    response = await client.get(
        f"/api/v1/blockchain/identities/guest/{guest_db.id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["guest_id"] == str(guest_db.id)


@pytest.mark.asyncio
async def test_list_identities(client: AsyncClient, manager_headers: dict, blockchain_identity_fixture):
    """DID'leri listele."""
    response = await client.get(
        "/api/v1/blockchain/identities",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_verify_identity(client: AsyncClient, manager_headers: dict, blockchain_identity_fixture):
    """DID doğrula."""
    identity_id = blockchain_identity_fixture["id"]
    response = await client.post(
        f"/api/v1/blockchain/identities/{identity_id}/verify",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["is_verified"] is True


# ── VC Tests ──

@pytest.mark.asyncio
async def test_issue_credential(client: AsyncClient, manager_headers: dict, blockchain_identity_fixture):
    """VC oluştur."""
    identity_id = blockchain_identity_fixture["id"]
    response = await client.post(
        "/api/v1/blockchain/credentials",
        json={
            "identity_id": identity_id,
            "credential_type": "PassportCredential",
            "credential_data": {"firstName": "JOHN", "lastName": "DOE", "nationality": "TR"},
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["credential_type"] == "PassportCredential"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_list_credentials(client: AsyncClient, manager_headers: dict, blockchain_identity_fixture):
    """VC'leri listele."""
    response = await client.get(
        "/api/v1/blockchain/credentials",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_revoke_credential(client: AsyncClient, manager_headers: dict, blockchain_identity_fixture):
    """VC iptal et."""
    identity_id = blockchain_identity_fixture["id"]

    # Create VC
    create_resp = await client.post(
        "/api/v1/blockchain/credentials",
        json={
            "identity_id": identity_id,
            "credential_type": "LoyaltyMembership",
            "credential_data": {"tier": "Gold"},
        },
        headers=manager_headers,
    )
    credential_id = create_resp.json()["id"]

    # Revoke
    response = await client.post(
        f"/api/v1/blockchain/credentials/{credential_id}/revoke",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["is_revoked"] is True


# ── Verification Proof Tests ──

@pytest.mark.asyncio
async def test_create_verification(client: AsyncClient, manager_headers: dict, blockchain_identity_fixture):
    """Doğrulama ispatı oluştur."""
    identity_id = blockchain_identity_fixture["id"]
    response = await client.post(
        "/api/v1/blockchain/verifications",
        json={
            "identity_id": identity_id,
            "verification_type": "age_verification",
            "disclosed_fields": {"over18": True},
            "verifier_id": "hotel_frontdesk",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "verified"


# ── Consent Tests ──

@pytest.mark.asyncio
async def test_log_consent(client: AsyncClient, manager_headers: dict, guest_db):
    """İzin kaydı oluştur."""
    response = await client.post(
        "/api/v1/blockchain/consent",
        json={
            "guest_id": str(guest_db.id),
            "consent_type": "blockchain_identity",
            "is_granted": True,
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["consent_type"] == "blockchain_identity"
    assert data["is_granted"] is True


@pytest.mark.asyncio
async def test_list_consents(client: AsyncClient, manager_headers: dict):
    """İzin kayıtlarını listele."""
    response = await client.get(
        "/api/v1/blockchain/consent",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
