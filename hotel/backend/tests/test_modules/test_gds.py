"""TASK-019 GDS Integration tests."""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def gds_channel_fixture(async_client, manager_headers):
    """Test GDS kanalı oluştur."""
    response = await async_client.post(
        "/api/v1/gds/channels",
        json={
            "code": "AMADEUS",
            "name": "Amadeus GDS",
            "provider": "amadeus",
            "supported_actions": {"search": True, "book": True, "cancel": True},
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    return response.json()


# ── Channel Tests ──

@pytest.mark.asyncio
async def test_create_channel(client: AsyncClient, manager_headers: dict):
    """Yeni GDS kanalı oluştur."""
    response = await client.post(
        "/api/v1/gds/channels",
        json={
            "code": "SABRE",
            "name": "Sabre GDS",
            "provider": "sabre",
            "supported_actions": {"search": True, "book": True, "cancel": True},
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "SABRE"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_channel(client: AsyncClient, manager_headers: dict, gds_channel_fixture):
    """Kanal detayını getir."""
    channel_id = gds_channel_fixture["id"]
    response = await client.get(
        f"/api/v1/gds/channels/{channel_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == channel_id


@pytest.mark.asyncio
async def test_update_channel(client: AsyncClient, manager_headers: dict, gds_channel_fixture):
    """Kanal bilgilerini güncelle."""
    channel_id = gds_channel_fixture["id"]
    response = await client.patch(
        f"/api/v1/gds/channels/{channel_id}",
        json={"name": "Amadeus GDS (Updated)", "is_active": False},
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Amadeus GDS (Updated)"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_list_channels(client: AsyncClient, manager_headers: dict, gds_channel_fixture):
    """Kanalları listele."""
    response = await client.get(
        "/api/v1/gds/channels",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_list_channels_by_provider(
    client: AsyncClient, manager_headers: dict, gds_channel_fixture
):
    """Kanalları provider'a göre filtrele."""
    response = await client.get(
        "/api/v1/gds/channels?provider=amadeus",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert all(c["provider"] == "amadeus" for c in data)


# ── Reservation Tests ──

@pytest.mark.asyncio
async def test_sync_reservation(client: AsyncClient, manager_headers: dict, gds_channel_fixture):
    """GDS rezervasyonu senkronize et."""
    channel_id = gds_channel_fixture["id"]
    response = await client.post(
        "/api/v1/gds/reservations/sync",
        json={
            "channel_id": channel_id,
            "gds_reservation_id": "AMA-123456",
            "guest_name": "John Doe",
            "guest_email": "john@example.com",
            "check_in": "2026-07-15",
            "check_out": "2026-07-18",
            "adults": 2,
            "room_type_code": "DBL",
            "rate_plan_code": "BAR",
            "total_amount": 450.00,
            "currency": "TRY",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["guest_name"] == "John Doe"
    assert data["gds_reservation_id"] == "AMA-123456"


@pytest.mark.asyncio
async def test_get_reservation(client: AsyncClient, manager_headers: dict, gds_channel_fixture):
    """GDS rezervasyon detayını getir."""
    channel_id = gds_channel_fixture["id"]

    # Create
    create_resp = await client.post(
        "/api/v1/gds/reservations/sync",
        json={
            "channel_id": channel_id,
            "gds_reservation_id": "AMA-789012",
            "guest_name": "Jane Doe",
            "check_in": "2026-08-01",
            "check_out": "2026-08-05",
            "adults": 1,
            "room_type_code": "SGL",
            "rate_plan_code": "BAR",
            "total_amount": 600.00,
        },
        headers=manager_headers,
    )
    res_id = create_resp.json()["id"]

    # Get
    response = await client.get(
        f"/api/v1/gds/reservations/{res_id}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["guest_name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_update_reservation(client: AsyncClient, manager_headers: dict, gds_channel_fixture):
    """GDS rezervasyon durumunu güncelle."""
    channel_id = gds_channel_fixture["id"]

    create_resp = await client.post(
        "/api/v1/gds/reservations/sync",
        json={
            "channel_id": channel_id,
            "gds_reservation_id": "AMA-345678",
            "guest_name": "Alice Smith",
            "check_in": "2026-09-01",
            "check_out": "2026-09-03",
            "adults": 2,
            "room_type_code": "DBL",
            "rate_plan_code": "BAR",
            "total_amount": 300.00,
        },
        headers=manager_headers,
    )
    res_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/gds/reservations/{res_id}",
        json={"status": "synced", "sync_message": "Rezervasyon başarıyla senkronize edildi"},
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "synced"


@pytest.mark.asyncio
async def test_list_reservations(client: AsyncClient, manager_headers: dict, gds_channel_fixture):
    """GDS rezervasyonlarını listele."""
    response = await client.get(
        "/api/v1/gds/reservations",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── Rate Mapping Tests ──

@pytest.mark.asyncio
async def test_create_rate_mapping(
    client: AsyncClient, manager_headers: dict, gds_channel_fixture, room_type_db
):
    """Rate mapping oluştur."""
    channel_id = gds_channel_fixture["id"]
    room_type_id = room_type_db.id

    response = await client.post(
        "/api/v1/gds/rate-mappings",
        json={
            "channel_id": channel_id,
            "gds_room_type_code": "DBL",
            "gds_rate_plan_code": "BAR",
            "hotel_room_type_id": str(room_type_id),
            "markup_percentage": 10.00,
        },
        headers=manager_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["gds_room_type_code"] == "DBL"
    assert data["markup_percentage"] == "10.00"


@pytest.mark.asyncio
async def test_list_rate_mappings(
    client: AsyncClient, manager_headers: dict, gds_channel_fixture, room_type_db
):
    """Rate mapping'leri listele."""
    response = await client.get(
        "/api/v1/gds/rate-mappings",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ── Sync Log Tests ──

@pytest.mark.asyncio
async def test_list_sync_logs(client: AsyncClient, manager_headers: dict, gds_channel_fixture):
    """Sync log'ları listele (rezervasyon sync otomatik log oluşturur)."""
    channel_id = gds_channel_fixture["id"]

    # Create a reservation to generate sync log
    await client.post(
        "/api/v1/gds/reservations/sync",
        json={
            "channel_id": channel_id,
            "gds_reservation_id": "AMA-901234",
            "guest_name": "Sync Log Test",
            "check_in": "2026-10-01",
            "check_out": "2026-10-05",
            "adults": 1,
            "room_type_code": "DBL",
            "rate_plan_code": "BAR",
            "total_amount": 500.00,
        },
        headers=manager_headers,
    )

    response = await client.get(
        "/api/v1/gds/sync-logs",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["action"] == "book"


@pytest.mark.asyncio
async def test_list_sync_logs_filtered(
    client: AsyncClient, manager_headers: dict, gds_channel_fixture
):
    """Sync log'larını filtreleyerek listele."""
    response = await client.get(
        "/api/v1/gds/sync-logs?action=book&status=success",
        headers=manager_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
