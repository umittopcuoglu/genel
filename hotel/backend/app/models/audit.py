"""
Audit log tablosu: Tüm yazma işlemlerinin kaydı (append-only).
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_action_resource", "action", "resource"),
        Index("ix_audit_logs_timestamp", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # POST, PUT, PATCH, DELETE
    resource: Mapped[str] = mapped_column(String(255), nullable=False)  # endpoint path
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<AuditLog {self.action} {self.resource} by {self.user_id}>"
