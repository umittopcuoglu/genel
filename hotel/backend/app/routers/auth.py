"""
Kimlik doğrulama endpoint'leri: login, refresh, logout.
"""
import os
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.db import get_db
from app.core.auth import (
    create_access_token, create_refresh_token,
    refresh_access_token, revoke_tokens
)
from app.core.rbac import require_roles
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, LogoutRequest, UserResponse
from app.models.user import User

_enabled = os.getenv("ENABLE_RATE_LIMIT", "true").lower() != "false"
limiter = Limiter(key_func=get_remote_address, enabled=_enabled)
router = APIRouter()

# Şifre hashleme context'i
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


@router.post("/login", response_model=TokenResponse, summary="Giriş yap", description="Email ve şifre ile giriş yaparak access ve refresh token alın.")
@limiter.limit("10/minute")
async def login(request: Request, login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Kullanıcıyı email ile bul (soft delete kontrolü)
    stmt = select(User).where(User.email == login_data.email, User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Geçersiz e-posta veya şifre.",
                    "details": {}
                }
            }
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "USER_INACTIVE",
                    "message": "Kullanıcı hesabı aktif değil. Lütfen yöneticinizle iletişime geçin.",
                    "details": {}
                }
            }
        )

    # Token payload'ları
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    # Refresh token'ı veritabanına kaydet (opsiyonel ama daha güvenli)
    from app.models.user import RefreshToken
    from datetime import datetime, timedelta, timezone
    new_refresh = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=False
    )
    db.add(new_refresh)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=TokenResponse, summary="Token yenile", description="Refresh token kullanarak yeni access token alın.")
@limiter.limit("20/minute")
async def refresh_token(request: Request, refresh_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    # Refresh token'ı doğrula ve yeni access token üret
    try:
        new_access_token = await refresh_access_token(refresh_data.refresh_token)
        # Aynı refresh token ile birlikte dön (opsiyonel olarak yeni refresh token da üretilebilir)
        # Bu örnekte refresh token değişmiyor, ancak güvenlik için rotasyon önerilir. Basit bırakıyoruz.
        # Kullanıcı bilgilerini refresh token'dan al
        from app.core.auth import verify_token
        import uuid as uuid_lib
        payload = await verify_token(refresh_data.refresh_token, token_type="refresh")
        user_id = uuid_lib.UUID(payload.get("sub"))
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise Exception("User not found")
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_data.refresh_token,
            user=UserResponse.model_validate(user)
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Geçersiz veya süresi dolmuş refresh token.",
                    "details": {}
                }
            }
        )


@router.post("/logout", summary="Çıkış yap", description="Access ve refresh token'ları iptal eder.")
async def logout(logout_data: LogoutRequest, db: AsyncSession = Depends(get_db)):
    # Token'ları blacklist'e ekle
    await revoke_tokens(logout_data.access_token, logout_data.refresh_token)

    # Veritabanındaki refresh token'ı revoked yap
    from app.models.user import RefreshToken
    stmt = select(RefreshToken).where(RefreshToken.token == logout_data.refresh_token)
    result = await db.execute(stmt)
    refresh_token_obj = result.scalar_one_or_none()
    if refresh_token_obj:
        refresh_token_obj.revoked = True
        await db.commit()

    return {"message": "Başarıyla çıkış yapıldı."}


@router.get("/users", summary="Kullanıcıları listele", tags=["Admin"])
async def list_users(db: AsyncSession = Depends(get_db), _=Depends(require_roles(["superadmin"]))):
    stmt = select(User).where(User.deleted_at.is_(None))
    result = await db.execute(stmt)
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/users", response_model=UserResponse, status_code=201, summary="Kullanıcı oluştur", tags=["Admin"])
async def create_user(
    user_data: dict, db: AsyncSession = Depends(get_db), _=Depends(require_roles(["superadmin"]))
):
    from pydantic import BaseModel
    class UserCreateRequest(BaseModel):
        email: str
        full_name: str
        password: str
        role: str = "frontdesk"

    data = UserCreateRequest(**user_data)
    stmt = select(User).where(User.email == data.email, User.deleted_at.is_(None))
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Kullanıcı zaten var")
    
    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        role=data.role,
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse, summary="Kullanıcı güncelle", tags=["Admin"])
async def update_user(
    user_id: str, updates: dict, db: AsyncSession = Depends(get_db), _=Depends(require_roles(["superadmin"]))
):
    import uuid
    stmt = select(User).where(User.id == uuid.UUID(user_id), User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    if "full_name" in updates:
        user.full_name = updates["full_name"]
    if "is_active" in updates:
        user.is_active = updates["is_active"]
    if "role" in updates:
        user.role = updates["role"]
    
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=204, summary="Kullanıcı sil", tags=["Admin"])
async def delete_user(
    user_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_roles(["superadmin"]))
):
    import uuid
    from datetime import datetime, timezone
    stmt = select(User).where(User.id == uuid.UUID(user_id), User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    user.deleted_at = datetime.now(timezone.utc)
    await db.commit()
