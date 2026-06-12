"""TASK-024 Mobile Check-in tests."""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def checkin_session_fixture(async_client, manager_headers, reservation_db, guest_db):
    """Test check-in oturumu oluştur."""
    response = await async_client.post(
        "/api/v1/mobile/checkin/start",
        json={
            "reservation_id": str(reservation_db.id),
            "guest_id": str(guest_db.id),
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    return response.json()


# ── Session Tests ──

@pytest.mark.asyncio
async def test_start_checkin(client: AsyncClient, manager_headers: dict, reservation_db, guest_db):
    """Check-in oturumu başlat."""
    response = await client.post(
        "/api/v1/mobile/checkin/start",
        json={
            "reservation_id": str(reservation_db.id),
            "guest_id": str(guest_db.id),
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "started"
    assert data["session_token"] is not None


@pytest.mark.asyncio
async def test_get_session(client: AsyncClient, manager_headers: dict, checkin_session_fixture):
    """Oturum detayını getir."""
    session_id = checkin_session_fixture["id"]
    response = await client.get(
        f"/api/v1/mobile/checkin/sessions/{session_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == session_id


@pytest.mark.asyncio
async def test_list_sessions(client: AsyncClient, manager_headers: dict, checkin_session_fixture):
    """Oturumları listele."""
    response = await client.get(
        "/api/v1/mobile/checkin/sessions",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_complete_checkin(client: AsyncClient, manager_headers: dict, checkin_session_fixture):
    """Check-in tamamla."""
    session_id = checkin_session_fixture["id"]
    response = await client.post(
        f"/api/v1/mobile/checkin/sessions/{session_id}/complete",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


# ── OCR Tests ──

@pytest.mark.asyncio
async def test_scan_document(client: AsyncClient, manager_headers: dict, guest_db):
    """Belge tara."""
    response = await client.post(
        "/api/v1/mobile/ocr/scan",
        json={
            "guest_id": str(guest_db.id),
            "scan_type": "passport",
            "document_number": "U12345678",
            "first_name": "JOHN",
            "last_name": "DOE",
            "nationality": "TR",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["scan_type"] == "passport"
    assert data["scan_confidence"] > 0


@pytest.mark.asyncio
async def test_list_document_scans(client: AsyncClient, manager_headers: dict, guest_db):
    """Taranan belgeleri listele."""
    response = await client.get(
        "/api/v1/mobile/ocr/scans",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── Face Recognition Tests ──

@pytest.mark.asyncio
async def test_scan_face(client: AsyncClient, manager_headers: dict, checkin_session_fixture, guest_db):
    """Yüz taraması yap."""
    session_id = checkin_session_fixture["id"]
    response = await client.post(
        f"/api/v1/mobile/checkin/sessions/{session_id}/face",
        params={"guest_id": str(guest_db.id)},
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["confidence_score"] > 0
    assert "is_match" in data


# ── EGM Tests ──

@pytest.mark.asyncio
async def test_submit_egm(client: AsyncClient, manager_headers: dict, stay_db, guest_db):
    """EGM bildirimi gönder."""
    response = await client.post(
        "/api/v1/mobile/egm/submit",
        params={"stay_id": str(stay_db.id), "guest_id": str(guest_db.id)},
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "submitted"
    assert data["reference_number"] is not None


@pytest.mark.asyncio
async def test_list_egm_submissions(client: AsyncClient, manager_headers: dict):
    """EGM bildirimlerini listele."""
    response = await client.get(
        "/api/v1/mobile/egm/submissions",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── NFC Key Tests ──

@pytest.mark.asyncio
async def test_issue_nfc_key(client: AsyncClient, manager_headers: dict, stay_db, room_db, guest_db):
    """NFC oda anahtarı oluştur."""
    response = await client.post(
        "/api/v1/mobile/nfc/keys",
        json={
            "stay_id": str(stay_db.id),
            "room_id": str(room_db.id),
            "guest_id": str(guest_db.id),
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "active"
    assert data["token"] is not None


@pytest.mark.asyncio
async def test_revoke_nfc_key(client: AsyncClient, manager_headers: dict, stay_db, room_db, guest_db):
    """NFC anahtarını iptal et."""
    # Create first
    create_resp = await client.post(
        "/api/v1/mobile/nfc/keys",
        json={
            "stay_id": str(stay_db.id),
            "room_id": str(room_db.id),
            "guest_id": str(guest_db.id),
        },
        headers=manager_headers,
    )
    key_id = create_resp.json()["id"]

    # Revoke
    response = await client.post(
        f"/api/v1/mobile/nfc/keys/{key_id}/revoke",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "revoked"
