"""
FastAPI uygulama giriş noktası.
Global exception handler, middleware (audit, CORS, vs.) ve router'ları içerir.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import uuid

from app.core.config import settings
from app.core.db import engine
from app.core.audit import AuditMiddleware
from app.routers import auth, health

# Logging yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama yaşam döngüsü: başlangıç ve kapanış işlemleri."""
    # Başlangıç
    logger.info("HotelOps PMS backend başlıyor...")
    # Veritabanı bağlantılarını kontrol et (opsiyonel)
    async with engine.begin() as conn:
        logger.info("Veritabanı bağlantısı başarılı.")
    yield
    # Kapanış
    logger.info("HotelOps PMS backend kapanıyor...")
    await engine.dispose()


app = FastAPI(
    title="HotelOps PMS API",
    description="AI destekli Otel Yönetim Sistemi Backend API",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# CORS ayarları (geliştirme için tüm originlere izin ver)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit middleware (tüm yazma işlemlerini logla)
app.add_middleware(AuditMiddleware)


# Global exception handler'lar
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Pydantic doğrulama hatalarını standart formata dönüştür."""
    details = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        details[field] = error["msg"]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "İstek verileri doğrulama hatası içeriyor.",
                "details": details
            }
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Genel hata yakalayıcı - beklenmeyen hataları logla ve 500 döndür."""
    logger.exception(f"Beklenmeyen hata: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Sunucuda bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
                "details": {}
            }
        }
    )


# Router'ları dahil et
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "HotelOps PMS API çalışıyor. /api/v1/docs adresine gidin."}
