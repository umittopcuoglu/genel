"""Misafir Wi-Fi Portal testleri."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guest_wifi_session import GuestWiFiSession, GuestWiFiStatus
from app.services.guest_wifi_service import GuestWiFiService


@pytest.mark.asyncio
async def test_guest_wifi_register_success(client: AsyncClient):
    """Misafir Wi-Fi başarılı kaydı."""
    response = await client.post(
        "/api/v1/guest-wifi/register",
        json={
            "email": "guest@example.com",
            "guest_name": "John Doe",
            "phone": "+1234567890",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["ssid"] == "HotelOps-Guest"
    assert len(data["password"]) == 12
    assert data["valid_hours"] == 24
    assert "valid_until" in data


@pytest.mark.asyncio
async def test_guest_wifi_register_terms_not_accepted(client: AsyncClient):
    """Koşul kabul etmeden Wi-Fi kaydı başarısız."""
    response = await client.post(
        "/api/v1/guest-wifi/register",
        json={
            "email": "guest@example.com",
            "guest_name": "John Doe",
            "phone": "+1234567890",
            "terms_accepted": False,
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_guest_wifi_register_invalid_email(client: AsyncClient):
    """Geçersiz e-posta ile Wi-Fi kaydı başarısız."""
    response = await client.post(
        "/api/v1/guest-wifi/register",
        json={
            "email": "invalid-email",
            "guest_name": "John Doe",
            "phone": "+1234567890",
            "terms_accepted": True,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_guest_wifi_get_status_success(client: AsyncClient):
    """Aktif Wi-Fi oturumunun durumunu getir."""
    # Önce kaydol
    await client.post(
        "/api/v1/guest-wifi/register",
        json={
            "email": "guest@example.com",
            "guest_name": "John Doe",
            "terms_accepted": True,
        },
    )

    # Durumu kontrol et
    response = await client.get("/api/v1/guest-wifi/status/guest@example.com")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "guest@example.com"
    assert data["status"] == "active"
    assert data["is_active"] is True
    assert data["remaining_hours"] > 0


@pytest.mark.asyncio
async def test_guest_wifi_get_status_not_found(client: AsyncClient):
    """Olmayan e-posta için durumu getir."""
    response = await client.get("/api/v1/guest-wifi/status/nonexistent@example.com")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_guest_wifi_resend_credentials(client: AsyncClient):
    """Kimlik bilgilerini tekrar gönder."""
    # Kaydol
    register_resp = await client.post(
        "/api/v1/guest-wifi/register",
        json={
            "email": "guest@example.com",
            "guest_name": "John Doe",
            "terms_accepted": True,
        },
    )
    original_password = register_resp.json()["password"]

    # Kimlik bilgilerini tekrar gönder
    response = await client.post(
        "/api/v1/guest-wifi/resend-credentials/guest@example.com"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "guest@example.com"
    assert data["wifi_password"] == original_password  # Aynı şifre


@pytest.mark.asyncio
async def test_guest_wifi_resend_credentials_not_found(client: AsyncClient):
    """Olmayan e-posta için kimlik bilgisi gönder."""
    response = await client.post(
        "/api/v1/guest-wifi/resend-credentials/nonexistent@example.com"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_guest_wifi_revoke_superadmin(client: AsyncClient, superadmin_headers: dict):
    """Superadmin tarafından Wi-Fi erişimi iptal."""
    # Kaydol
    await client.post(
        "/api/v1/guest-wifi/register",
        json={
            "email": "guest@example.com",
            "guest_name": "John Doe",
            "terms_accepted": True,
        },
    )

    # İptal et
    response = await client.delete(
        "/api/v1/guest-wifi/revoke/guest@example.com",
        headers=superadmin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Durumunu kontrol et (artık aktif olmamalı)
    status_resp = await client.get("/api/v1/guest-wifi/status/guest@example.com")
    assert status_resp.status_code == 404


@pytest.mark.asyncio
async def test_guest_wifi_revoke_without_auth(client: AsyncClient):
    """Auth olmadan Wi-Fi iptal işlemi başarısız."""
    response = await client.delete("/api/v1/guest-wifi/revoke/guest@example.com")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_guest_wifi_revoke_not_found(client: AsyncClient, superadmin_headers: dict):
    """Olmayan e-posta için iptal işlemi."""
    response = await client.delete(
        "/api/v1/guest-wifi/revoke/nonexistent@example.com",
        headers=superadmin_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_guest_wifi_duplicate_registration_revokes_old(
    client: AsyncClient,
    db: AsyncSession,
):
    """Aynı e-posta ile yeniden kaydolunca eski oturum iptal edilir."""
    # İlk kayıt
    resp1 = await client.post(
        "/api/v1/guest-wifi/register",
        json={
            "email": "guest@example.com",
            "guest_name": "John Doe",
            "terms_accepted": True,
        },
    )
    password1 = resp1.json()["password"]

    # İkinci kayıt
    resp2 = await client.post(
        "/api/v1/guest-wifi/register",
        json={
            "email": "guest@example.com",
            "guest_name": "Jane Doe",
            "terms_accepted": True,
        },
    )
    password2 = resp2.json()["password"]

    # Şifreler farklı olmalı
    assert password1 != password2

    # Veritabanında eski oturum revoked, yeni oturum active olmalı
    from sqlalchemy import select

    sessions = await db.scalars(
        select(GuestWiFiSession)
        .where(GuestWiFiSession.email == "guest@example.com")
        .where(GuestWiFiSession.deleted_at.is_(None))
    )
    sessions_list = list(sessions)
    assert len(sessions_list) == 2
    assert sum(1 for s in sessions_list if s.status == GuestWiFiStatus.active) == 1
    assert sum(1 for s in sessions_list if s.status == GuestWiFiStatus.revoked) == 1


@pytest.mark.asyncio
async def test_guest_wifi_service_password_generation():
    """Wi-Fi şifresi üretimi test."""
    pwd1 = GuestWiFiService._generate_wifi_password()
    pwd2 = GuestWiFiService._generate_wifi_password()

    assert len(pwd1) == 12
    assert len(pwd2) == 12
    assert pwd1 != pwd2  # Rastgele olmalı
    assert pwd1.isalnum()  # Yalnız harf + sayı
    assert pwd2.isalnum()
