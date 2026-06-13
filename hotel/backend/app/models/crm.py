"""CRM modelleri: Segment, Campaign, GuestNote, CommunicationLog."""
import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Uuid, Text, Integer, JSON
from sqlalchemy.types import Numeric as SA_Decimal
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    CANCELLED = "cancelled"


class CampaignChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"


class Segment(BaseModel):
    """Dinamik misafir segmenti — kriter JSON olarak saklanır.

    Örnek criteria:
      {"min_stays": 3, "min_lifetime_revenue": 5000, "tiers": ["gold","platinum"]}
    """
    __tablename__ = "crm_segments"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criteria: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Campaign(BaseModel):
    """Pazarlama/iletişim kampanyası."""
    __tablename__ = "crm_campaigns"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default=CampaignChannel.EMAIL.value)
    subject: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    segment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("crm_segments.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=CampaignStatus.DRAFT.value)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delivered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class GuestNote(BaseModel):
    """Misafir profilinde tutulan operasyonel notlar (alerji, tercih, VIP açıklaması)."""
    __tablename__ = "crm_guest_notes"

    guest_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("guests.id"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="general")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class CommunicationLog(BaseModel):
    """Misafir ile yapılan tüm iletişimlerin kaydı (email/sms/whatsapp/çağrı)."""
    __tablename__ = "crm_communication_logs"

    guest_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("guests.id"), nullable=False, index=True
    )
    campaign_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("crm_campaigns.id"), nullable=True, index=True
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False, default="outbound")  # inbound/outbound
    subject: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="sent")  # sent/delivered/failed/read
    external_ref: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
