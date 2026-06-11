"""
Kullanıcı ve rol modelleri (RBAC).
RefreshToken modeli de burada tanımlanır.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel
from app.core.db import Base
from app.core.rbac import ALL_ROLES


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="guest")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # İlişkiler
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class RefreshToken(Base):
    """Refresh token'ları veritabanında tutmak için (opsiyonel, ek güvenlik)."""
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_tokens_token", "token"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        BaseModel.__annotations__["id"].type,
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        BaseModel.__annotations__["id"].type,
        nullable=False,
        index=True
    )
    token: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)

    # İlişkiler
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
