from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


# ── VoiceIntegration ──

class VoiceIntegrationResponse(BaseModel):
    id: UUID
    room_id: UUID
    provider: str
    device_id: str
    device_name: str
    is_active: bool
    locale: str
    config: Optional[dict] = None
    last_interaction_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class VoiceIntegrationCreate(BaseModel):
    room_id: UUID
    provider: str = Field(..., max_length=20)
    device_id: str = Field(..., max_length=100)
    device_name: str = Field(..., max_length=100)
    locale: str = "tr-TR"
    config: Optional[dict] = None
    notes: Optional[str] = None


class VoiceIntegrationUpdate(BaseModel):
    is_active: Optional[bool] = None
    locale: Optional[str] = None
    config: Optional[dict] = None
    notes: Optional[str] = None


# ── VoiceCommand ──

class VoiceCommandResponse(BaseModel):
    id: UUID
    integration_id: UUID
    session_id: Optional[str] = None
    intent: str
    raw_text: str
    confidence: Optional[float] = None
    parameters: Optional[dict] = None
    result: Optional[str] = None
    response_text: Optional[str] = None
    executed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    class Config:
        from_attributes = True


# ── VoiceSession ──

class VoiceSessionResponse(BaseModel):
    id: UUID
    integration_id: UUID
    session_id: str
    provider: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    context: Optional[dict] = None
    command_count: int

    class Config:
        from_attributes = True


# ── VoiceInteraction ──

class VoiceInteractionResponse(BaseModel):
    id: UUID
    integration_id: UUID
    direction: str
    provider: str
    request_type: str
    raw_request: Optional[dict] = None
    raw_response: Optional[dict] = None
    status_code: Optional[int] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


# ── VoiceIntentsMapping ──

class VoiceIntentsMappingResponse(BaseModel):
    id: UUID
    provider: str
    intent_name: str
    action: str
    action_params_template: Optional[dict] = None
    is_active: bool
    description: Optional[str] = None

    class Config:
        from_attributes = True


class VoiceIntentsMappingCreate(BaseModel):
    provider: str = Field(..., max_length=20)
    intent_name: str = Field(..., max_length=100)
    action: str = Field(..., max_length=50)
    action_params_template: Optional[dict] = None
    description: Optional[str] = None


# ── Webhook ──

class AlexaWebhookRequest(BaseModel):
    """Alexa skill webhook girişi."""
    version: str = "1.0"
    session: dict
    request: dict
    context: Optional[dict] = None


class GoogleWebhookRequest(BaseModel):
    """Google Actions webhook girişi."""
    user: dict
    conversation: dict
    inputs: list[dict]


class WebhookResponse(BaseModel):
    """Webhook çıkışı (Alexa/Google)."""
    version: str = "1.0"
    response: dict
    session_attributes: Optional[dict] = None
