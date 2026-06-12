"""
Entegrasyon Ayarları modeli: GİB e-Fatura, OTA, GDS, WhatsApp, IoT gibi dış
entegrasyonların parametreleri admin tarafından çalışma zamanında girilir.
Hassas parametreler (API anahtarı, parola, token) şifreli saklanır.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class IntegrationSetting(BaseModel):
    """Tek bir dış entegrasyon kaydı (tip + parametre seti)."""
    __tablename__ = "integration_settings"

    # gib_einvoice, ota_channel, gds, whatsapp, iot
    integration_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Fernet ile şifrelenmiş JSON parametre sözlüğü
    params_encrypted: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Son bağlantı testi sonucu
    last_test_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_ok: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    last_test_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<IntegrationSetting {self.integration_type}:{self.name} enabled={self.enabled}>"
