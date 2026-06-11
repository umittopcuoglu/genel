"""
JWT token üretme, doğrulama, kullanıcı alımı ve refresh token yönetimi.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis

from app.core.config import settings
from app.core.db import get_db
from app.models.user import User, RefreshToken

security = HTTPBearer(auto_error=False)

# Redis bağlantısı (blacklist için)
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Access token oluşturur. Varsayılan süre 15 dakika."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Refresh token oluşturur. Varsayılan süre 7 gün."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


async def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """Token'ı doğrular ve payload'ı döndürür. Geçersizse HTTPException fırlatır."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "INVALID_TOKEN",
                "message": "Geçersiz veya süresi dolmuş token.",
                "details": {}
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != token_type:
            raise credentials_exception
        # Blacklist kontrolü (sadece access token için yapılabilir)
        if token_type == "access":
            is_blacklisted = await redis_client.get(f"blacklist:access:{token}")
            if is_blacklisted:
                raise credentials_exception
        return payload
    except jwt.PyJWTError:
        raise credentials_exception


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Mevcut kullanıcıyı token'dan alır. Dependency olarak kullanılır."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "MISSING_TOKEN",
                    "message": "Yetkilendirme token'ı eksik.",
                    "details": {}
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = await verify_token(token, token_type="access")
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": "Token içinde kullanıcı bilgisi yok.",
                    "details": {}
                }
            }
        )
    # Kullanıcıyı veritabanından al (soft delete kontrolü)
    stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "Kullanıcı bulunamadı veya pasif durumda.",
                    "details": {}
                }
            }
        )
    return user


async def refresh_access_token(refresh_token: str) -> str:
    """Refresh token kullanarak yeni access token üretir."""
    payload = await verify_token(refresh_token, token_type="refresh")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Geçersiz refresh token.",
                    "details": {}
                }
            }
        )
    # Refresh token'ın veritabanında geçerli olup olmadığını kontrol et (revoke edilmemiş)
    # Not: Burada basitçe blacklist kontrolü yapılabilir. Daha sıkı güvenlik için veritabanında refresh token modeli de tutulabilir.
    # Örnek: RefreshToken tablosundan kontrol et
    # Kısa kesmek için sadece Redis blacklist kullanıyoruz.
    is_blacklisted = await redis_client.get(f"blacklist:refresh:{refresh_token}")
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "REFRESH_TOKEN_REVOKED",
                    "message": "Refresh token iptal edilmiş.",
                    "details": {}
                }
            }
        )
    new_access_token = create_access_token({"sub": user_id})
    return new_access_token


async def revoke_tokens(access_token: str, refresh_token: str):
    """Kullanıcının access ve refresh token'larını blacklist'e ekler (logout)."""
    # Sürelerini almak için token'ları decode et (exp süresini al)
    try:
        access_payload = jwt.decode(access_token, options={"verify_signature": False})
        refresh_payload = jwt.decode(refresh_token, options={"verify_signature": False})
        access_exp = access_payload.get("exp")
        refresh_exp = refresh_payload.get("exp")
        if access_exp:
            ttl = max(0, access_exp - int(datetime.now(timezone.utc).timestamp()))
            await redis_client.setex(f"blacklist:access:{access_token}", ttl, "1")
        if refresh_exp:
            ttl = max(0, refresh_exp - int(datetime.now(timezone.utc).timestamp()))
            await redis_client.setex(f"blacklist:refresh:{refresh_token}", ttl, "1")
    except Exception:
        # Hata durumunda sessiz geç
        pass
