"""
Auth endpoint'leri için pytest testleri:
- login happy path
- login yanlış şifre
- refresh token
- expired token (simülasyon)
- RBAC 403 (korunan endpoint'e yetkisiz rol)
"""
import pytest
from datetime import datetime, timedelta, timezone
import jwt
from httpx import AsyncClient
from app.core.config import settings
from app.core.auth import create_access_token


@pytest.mark.asyncio
async def test_login_happy(async_client: AsyncClient, test_superadmin):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.com", "password": "Admin123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "superadmin@test.com"
    assert data["user"]["role"] == "superadmin"


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient, test_superadmin):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.com", "password": "WrongPass!"}
    )
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "INVALID_CREDENTIALS"
    assert "Geçersiz e-posta veya şifre" in error["message"]


@pytest.mark.asyncio
async def test_refresh_token(async_client: AsyncClient, test_superadmin):
    # Önce login yap
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.com", "password": "Admin123!"}
    )
    refresh_token = login_resp.json()["refresh_token"]
    # Refresh endpoint
    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["refresh_token"] == refresh_token
    assert data["user"]["email"] == "superadmin@test.com"


@pytest.mark.asyncio
async def test_refresh_invalid_token(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.token.here"}
    )
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "INVALID_TOKEN"  # verify_token'dan gelir


@pytest.mark.asyncio
async def test_expired_access_token(async_client: AsyncClient, test_superadmin):
    # Süresi geçmiş access token oluştur
    expired = datetime.now(timezone.utc) - timedelta(minutes=1)
    expired_token = jwt.encode(
        {"sub": str(test_superadmin.id), "exp": expired, "type": "access"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    # Süresi dolmuş token'ın reddedildiğini doğrula
    from app.core.auth import verify_token
    with pytest.raises(Exception):
        await verify_token(expired_token, "access")
    # Test geçer
    assert True


@pytest.mark.asyncio
async def test_rbac_403(async_client: AsyncClient, test_frontdesk):
    # frontdesk rolü ile login yap
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "frontdesk@test.com", "password": "Front123!"}
    )
    access_token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # superadmin gerektiren bir endpoint yok henüz; require_roles dependency'sini doğrudan test et.
    from app.core.rbac import require_roles

    test_user = test_frontdesk
    allowed = ["superadmin"]
    checker = require_roles(allowed)
    with pytest.raises(Exception) as exc_info:
        await checker(test_user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["error"]["code"] == "INSUFFICIENT_PERMISSIONS"
