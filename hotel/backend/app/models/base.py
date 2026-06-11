"""
Base model sınıfı: Tüm tabloların ortak alanlarını içerir.
Soft delete (deleted_at), created_by, updated_by, id (UUID), timestamps.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr, Mapped, mapped_column
from app.core.db import Base
from app.core.audit import get_current_user_id_from_context


class BaseModel(Base):
    """Tüm modellerin türeyeceği temel sınıf."""
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
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
        String(36), nullable=True  # UUID string format
    )
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
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
