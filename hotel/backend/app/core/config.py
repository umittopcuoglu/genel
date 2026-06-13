"""
Uygulama konfigürasyonu: .env dosyasından okunan ayarlar.
Pydantic Settings kullanımı.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict
from typing import List


class Settings(BaseSettings):
    """Uygulama ayarları."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Uygulama
    APP_NAME: str = "HotelOps PMS"
    DEBUG: bool = False

    # Veritabanı
    # FB-001 Bulgu 7: test-dostu güvenli default'lar — production .env ile override eder.
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Redis (opsiyonel, blacklist için)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Log seviyesi
    LOG_LEVEL: str = "INFO"


settings = Settings()
