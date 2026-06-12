"""Entegrasyon Ayarları şemaları."""
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field

IntegrationType = Literal["gib_einvoice", "ota_channel", "gds", "whatsapp", "iot", "payment_gateway"]

# Tip başına beklenen parametre tanımları (frontend form üretimi için)
PARAM_SPECS: dict[str, list[dict]] = {
    "gib_einvoice": [
        {"key": "provider", "label": "Entegratör", "type": "select",
         "options": ["foriba", "logo", "uyumsoft", "izibiz", "diger"], "required": True},
        {"key": "username", "label": "Kullanıcı Adı", "type": "text", "required": True},
        {"key": "password", "label": "Parola", "type": "secret", "required": True},
        {"key": "vkn", "label": "VKN / TCKN", "type": "text", "required": True},
        {"key": "endpoint_url", "label": "Servis URL", "type": "url", "required": True},
        {"key": "environment", "label": "Ortam", "type": "select", "options": ["test", "prod"], "required": True},
    ],
    "ota_channel": [
        {"key": "channel", "label": "Kanal", "type": "select",
         "options": ["booking", "expedia", "airbnb", "etstur", "diger"], "required": True},
        {"key": "api_key", "label": "API Anahtarı", "type": "secret", "required": True},
        {"key": "hotel_code", "label": "Otel Kodu", "type": "text", "required": True},
        {"key": "endpoint_url", "label": "API URL", "type": "url", "required": True},
        {"key": "commission_pct", "label": "Komisyon %", "type": "number", "required": False},
    ],
    "gds": [
        {"key": "provider", "label": "Sağlayıcı", "type": "select",
         "options": ["amadeus", "sabre", "travelport"], "required": True},
        {"key": "pcc", "label": "PCC Kodu", "type": "text", "required": True},
        {"key": "api_key", "label": "API Anahtarı", "type": "secret", "required": True},
        {"key": "api_secret", "label": "API Secret", "type": "secret", "required": True},
        {"key": "endpoint_url", "label": "Endpoint URL", "type": "url", "required": True},
    ],
    "whatsapp": [
        {"key": "access_token", "label": "Meta Access Token", "type": "secret", "required": True},
        {"key": "phone_number_id", "label": "Telefon Numarası ID", "type": "text", "required": True},
        {"key": "webhook_secret", "label": "Webhook Secret", "type": "secret", "required": True},
        {"key": "business_account_id", "label": "Business Account ID", "type": "text", "required": False},
    ],
    "payment_gateway": [
        {"key": "provider", "label": "Sağlayıcı", "type": "select",
         "options": ["iyzico", "stripe", "paytr", "craftgate", "param"], "required": True},
        {"key": "api_key", "label": "API Anahtarı", "type": "secret", "required": True},
        {"key": "secret_key", "label": "Secret Key", "type": "secret", "required": True},
        {"key": "endpoint_url", "label": "API URL", "type": "url", "required": True},
        {"key": "use_3d_secure", "label": "3D Secure Zorunlu", "type": "boolean", "required": False},
        {"key": "currency", "label": "Para Birimi", "type": "select", "options": ["TRY", "EUR", "USD"], "required": False},
    ],
    "iot": [
        {"key": "broker_host", "label": "MQTT Broker IP/Host", "type": "text", "required": True},
        {"key": "broker_port", "label": "Broker Port", "type": "number", "required": True},
        {"key": "username", "label": "Kullanıcı Adı", "type": "text", "required": False},
        {"key": "password", "label": "Parola", "type": "secret", "required": False},
        {"key": "use_tls", "label": "TLS Kullan", "type": "boolean", "required": False},
    ],
}


class IntegrationCreate(BaseModel):
    integration_type: IntegrationType
    name: str = Field(min_length=2, max_length=100)
    enabled: bool = False
    params: dict = Field(default_factory=dict)
    notes: Optional[str] = None


class IntegrationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    enabled: Optional[bool] = None
    # Kısmi güncelleme: sadece gönderilen anahtarlar üzerine yazılır;
    # maskeli değer ("••••") gönderilirse mevcut değer korunur.
    params: Optional[dict] = None
    notes: Optional[str] = None


class IntegrationResponse(BaseModel):
    id: UUID
    integration_type: str
    name: str
    enabled: bool
    params: dict  # maskelenmiş
    last_test_at: Optional[datetime] = None
    last_test_ok: Optional[bool] = None
    last_test_message: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class IntegrationTestResult(BaseModel):
    ok: bool
    message: str
    tested_at: datetime
