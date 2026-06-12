"""
Voice Control modelleri: Alexa/Google Asistan entegrasyonu, sesli komutlar.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Boolean, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class VoiceIntegration(BaseModel):
    """Sesli asistan entegrasyon kaydı (Alexa/Google)."""
    __tablename__ = "voice_integrations"

    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)  # alexa, google_assistant
    device_id: Mapped[str] = mapped_column(String(100), nullable=False)
    device_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    locale: Mapped[str] = mapped_column(String(10), default="tr-TR", nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    last_interaction_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<VoiceIntegration {self.provider} in Room {self.room_id}>"


class VoiceCommand(BaseModel):
    """Sesli komut kaydı."""
    __tablename__ = "voice_commands"

    integration_id: Mapped[str] = mapped_column(ForeignKey("voice_integrations.id"), nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    intent: Mapped[str] = mapped_column(String(50), nullable=False)  # set_temperature, turn_light, call_housekeeping, order_room_service, etc.
    raw_text: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    result: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # success, failed, not_understood
    response_text: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    performed_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    def __repr__(self) -> str:
        return f"<VoiceCommand {self.intent}: {self.raw_text[:50]}>"


class VoiceSession(BaseModel):
    """Sesli etkileşim oturumu."""
    __tablename__ = "voice_sessions"

    integration_id: Mapped[str] = mapped_column(ForeignKey("voice_integrations.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # active, completed, expired, error
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    command_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<VoiceSession {self.session_id[:20]} ({self.status})>"


class VoiceInteraction(BaseModel):
    """Sesli asistan ile etkileşim logu (webhook gelen/giden)."""
    __tablename__ = "voice_interactions"

    integration_id: Mapped[str] = mapped_column(ForeignKey("voice_integrations.id"), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # incoming, outgoing
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    request_type: Mapped[str] = mapped_column(String(30), nullable=False)  # intent_request, session_ended, launch_request
    raw_request: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    raw_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<VoiceInteraction {self.provider} {self.direction}>"


class VoiceIntentsMapping(BaseModel):
    """Sesli asistan intent → sistem aksiyonu eşleştirmesi."""
    __tablename__ = "voice_intents_mappings"

    provider: Mapped[str] = mapped_column(String(20), nullable=False)  # alexa, google_assistant
    intent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # set_temperature, call_housekeeping, etc.
    action_params_template: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"device_type": "thermostat", "command": "set_temperature"}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    def __repr__(self) -> str:
        return f"<VoiceIntentsMapping {self.provider}/{self.intent_name}>"
