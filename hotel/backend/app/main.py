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

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.db import engine
from app.core.audit import AuditMiddleware
from app.routers import auth, health, front_office, reservations, rate_plans, availability, folios, night_audit, reports, housekeeping, lost_found, minibar, currency
# Faz 2 router'ları (Channel Manager, CRM, Loyalty, AI, özel raporlar)
from app.routers import channels, complaints, feedback, loyalty, ai_endpoints, custom_reports
# Faz 3 router'ları (Groups & Events, Maintenance, HR, GDS, IoT)
from app.routers import groups, maintenance, hr, gds, iot
# Faz 4 router'ları (Computer Vision)
from app.routers import cv_inspections
# Faz 4 router'ları (Voice Control)
from app.routers import voice_webhooks
# Faz 4 router'ları (Multi-Property)
from app.routers import console
# Faz 4 router'ları (Mobile Check-in)
from app.routers import mobile_checkin
# Faz 4 router'ları (Blockchain Identity)
from app.routers import blockchain
# Entegrasyon Ayarları (parametrik GİB/OTA/GDS/WhatsApp/IoT)
from app.routers import integrations
# Booking Engine (public, komisyonsuz doğrudan satış)
from app.routers import booking_engine
# Misafir Wi-Fi Portal (public kayıt + self-service)
from app.routers import guest_wifi
# Payment Gateway (Stripe/iyzico/PayTR — parametrik provider)
from app.routers import payments
# CRM (Guest 360, Segment, Campaign, Notes, Communication)
from app.routers import crm
# WhatsApp Business API (Meta Cloud)
from app.routers import whatsapp
# GİB e-Fatura (Foriba/Logo/Uyumsoft/İzibiz)
from app.routers import einvoice
# Revenue Management / RevenueIQ
from app.routers import revenue
# F&B / POS (Outlet, Menu, Check)
from app.routers import fnb
# Güvenlik & KVKK (Access logs + Consent + Data Subject Requests)
from app.routers import security as security_router
# InsightAI (KPI özet + kanal mix + aksiyon önerileri)
from app.routers import insights
# Domain event abonelikleri (modular monolith iletişim katmanı)
from app.core import event_handlers  # noqa: F401  — import = subscribe

# Logging yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama yaşam döngüsü: başlangıç ve kapanış işlemleri."""
    # Başlangıç
    logger.info("HotelOps PMS backend başlıyor...")
    # AI ajanlarını registry'ye kaydet (RevenueQA, GuestAI, InsightAI, ShiftAI, EventIQ, vb.)
    from app.core.agents.init_agents import initialize_agents
    initialize_agents()
    # Veritabanı tablolarını oluştur + demo seed (Cloud Run cold start)
    import app.models  # noqa: F811 — tüm modelleri Base.metadata'ya kaydeder
    from app.core.db import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Veritabanı tabloları oluşturuldu/doğrulandı.")
    # Demo kullanıcıları seed et (yoksa)
    try:
        from sqlalchemy import select, func
        from app.models.user import User
        from app.core.db import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            count = await session.scalar(select(func.count()).select_from(User))
            if count == 0:
                from passlib.context import CryptContext
                pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
                demo_users = [
                    ("superadmin@hotelops.com", "Super Admin", "superadmin", "Super123!"),
                    ("manager@hotelops.com", "Manager User", "manager", "Manager123!"),
                    ("frontdesk@hotelops.com", "Front Desk", "frontdesk", "Front123!"),
                ]
                for email, name, role, password in demo_users:
                    session.add(User(email=email, hashed_password=pwd.hash(password),
                                     full_name=name, role=role, is_active=True))
                await session.commit()
                logger.info("Demo kullanıcıları seed edildi (3 kullanıcı).")
    except Exception as e:
        logger.warning(f"Seed atlandı: {e}")
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
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audit middleware (tüm yazma işlemlerini logla)
app.add_middleware(AuditMiddleware)

# Rate limiting (auth endpoint'leri)
from app.routers.auth import limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Global exception handler'lar
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """FB-001 ek bulgu: HTTPException(detail={"error": ...}) FastAPI tarafından
    {"detail": {...}} içine sarılıyordu — sözleşme {"error": ...} zarfı ister (02 §0.7).
    Bu handler zarfı düzleştirir; düz string detail'leri de zarfa çevirir."""
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        content = exc.detail
    else:
        content = {
            "error": {
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
                "details": {}
            }
        }
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=getattr(exc, "headers", None),
    )


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
app.include_router(front_office.router, prefix="/api/v1/front-office", tags=["Front Office"])
app.include_router(reservations.router, prefix="/api/v1", tags=["Reservations"])
app.include_router(rate_plans.router, prefix="/api/v1", tags=["Rate Plans"])
app.include_router(availability.router, prefix="/api/v1", tags=["Availability"])
app.include_router(folios.router, prefix="/api/v1", tags=["Finance"])
app.include_router(night_audit.router, prefix="/api/v1", tags=["Night Audit"])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"])
app.include_router(housekeeping.router, prefix="/api/v1", tags=["Housekeeping"])
app.include_router(lost_found.router, prefix="/api/v1", tags=["Lost & Found"])
app.include_router(minibar.router, prefix="/api/v1", tags=["Minibar"])
app.include_router(currency.router, tags=["Currency"])
# Faz 2 router kayıtları
app.include_router(channels.router, prefix="/api/v1", tags=["Channels"])
app.include_router(complaints.router, prefix="/api/v1", tags=["Complaints"])
app.include_router(feedback.router, prefix="/api/v1", tags=["Feedback"])
app.include_router(loyalty.router, prefix="/api/v1", tags=["Loyalty"])
app.include_router(ai_endpoints.router, prefix="/api/v1", tags=["AI"])
app.include_router(custom_reports.router, prefix="/api/v1", tags=["Reports"])
# Faz 3 router kayıtları (router'lar kendi tam prefix'ini taşıyor: /api/v1/groups vb.)
app.include_router(groups.router, tags=["Groups"])
app.include_router(maintenance.router, tags=["Maintenance"])
app.include_router(hr.router)
app.include_router(gds.router)
app.include_router(iot.router)
# Faz 4 router kayıtları
app.include_router(cv_inspections.router)
app.include_router(voice_webhooks.router)
app.include_router(console.router)
app.include_router(mobile_checkin.router)
app.include_router(blockchain.router)
app.include_router(integrations.router)
app.include_router(booking_engine.router)
app.include_router(guest_wifi.router)
app.include_router(payments.router)
app.include_router(crm.router)
app.include_router(whatsapp.router)
app.include_router(einvoice.router)
app.include_router(revenue.router)
app.include_router(fnb.router)
app.include_router(security_router.router)
app.include_router(insights.router)


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "HotelOps PMS API çalışıyor. /api/v1/docs adresine gidin."}
