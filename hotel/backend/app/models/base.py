"""
Base model sınıfı: Tüm tabloların ortak alanlarını içerir.
Soft delete (deleted_at), created_by, updated_by, id (UUID), timestamps.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Uuid, text, TypeDecorator
from sqlalchemy.orm import declared_attr, Mapped, mapped_column
from app.core.db import Base


class GUIDString(TypeDecorator):
    """created_by/updated_by için: UUID nesnesi veya str kabul eder, str(36) saklar.
    Audit context str döndürür; testler UUID nesnesi geçirir — ikisi de çalışır."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None


class BaseModel(Base):
    """Tüm modellerin türeyeceği temel sınıf."""
    __abstract__ = True

    # FB-001 Bulgu 5: dialect-bağımsız Uuid tipi (SQLite testlerde de çalışır);
    # gen_random_uuid() server_default kaldırıldı, Python tarafı default yeterli.
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        GUIDString(), nullable=True  # UUID string format (UUID veya str kabul eder)
    )
    updated_by: Mapped[Optional[str]] = mapped_column(
        GUIDString(), nullable=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def soft_delete(self):
        """Soft delete işlemi."""
        self.deleted_at = datetime.now()

    @classmethod
    def __declare_last__(cls):
        """Model event listener'ları ekle: created_by ve updated_by otomatik doldurma."""
        from sqlalchemy import event
        # Lazy import: circular import'u önler (base ↔ core.audit ↔ models.audit)
        from app.core.audit import get_current_user_id_from_context

        @event.listens_for(cls, 'before_insert', propagate=True)
        def before_insert(mapper, connection, target):
            if target.created_by is None:
                user_id = get_current_user_id_from_context()
                if user_id:
                    target.created_by = user_id
            if target.updated_by is None:
                user_id = get_current_user_id_from_context()
                if user_id:
                    target.updated_by = user_id

        @event.listens_for(cls, 'before_update', propagate=True)
        def before_update(mapper, connection, target):
            user_id = get_current_user_id_from_context()
            if user_id:
                target.updated_by = user_id
