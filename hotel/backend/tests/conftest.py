"""
Pytest yapılandırması: async test client, test veritabanı, global fixture'lar.
"""
import os
# Testlerde LLM ajanları mock moda düşsün (gerçek API anahtarı gerekmez)
os.environ.setdefault("ENABLE_LLM_MOCK", "true")
os.environ.setdefault("ENABLE_RATE_LIMIT", "false")

import asyncio
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.core.db import get_db, Base
from app.core.config import settings
# Import all models to ensure tables are created during test setup
from app.models import user, audit, front_office, reservation_ext, housekeeping, finance
from app.models import channel, channel_mapping, channel_sync_log, groups, maintenance, iot
from app.models import voice, mobile_checkin, cv, blockchain_identity, gds, hr, ai_invocation
from app.models import integration_setting, chat_session, chat_message, guest_wifi_session
from app.models import loyalty_account, loyalty_transaction, complaint, feedback, occupancy_forecast
from app.models import rate_recommendation, overbooking_rule, budget, ledger_entry, chart_of_accounts, einvoice, custom_report
# Specific model imports for fixtures
from app.models.user import User
from app.models.front_office import RoomType, Room, Guest, Reservation, Stay, Trace
from app.models.reservation_ext import RatePlan, Availability
from datetime import date, timedelta
from app.routers.auth import get_password_hash

# FB-001 Bulgu 4/5: testlerde gerçek Redis yok — fakeredis ile blacklist simüle edilir.
import fakeredis.aioredis
from app.core import auth as auth_module
auth_module.redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)

# Test veritabanı URL'i (SQLite in-memory ile hızlı test, ancak PostgreSQL özellikleri için ayrı test db kullanılabilir)
# Burada basitlik için SQLite kullanıyoruz; ancak UUID ve diğer özellikler çalışır.
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
# Eğer PostgreSQL test db varsa şu şekilde değiştirilebilir:
# TEST_DATABASE_URL = "postgresql+asyncpg://hotelops_test:testpass@localhost:5432/hotelops_test"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Her testten önce tabloları oluştur, sonra temizle."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Test için HTTPX async client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_superadmin(db: AsyncSession):
    """Test süperadmin kullanıcısı oluştur."""
    user = User(
        email="superadmin@test.com",
        hashed_password=get_password_hash("Admin123!"),
        full_name="Test Superadmin",
        role="superadmin",
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def test_manager(db: AsyncSession):
    user = User(
        email="manager@test.com",
        hashed_password=get_password_hash("Manager123!"),
        full_name="Test Manager",
        role="manager",
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def test_frontdesk(db: AsyncSession):
    user = User(
        email="frontdesk@test.com",
        hashed_password=get_password_hash("Front123!"),
        full_name="Test Frontdesk",
        role="frontdesk",
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def superadmin_token(async_client, test_superadmin):
    """Superadmin login token'i."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.com", "password": "Admin123!"}
    )
    return response.json()["access_token"]


@pytest.fixture
async def frontdesk_token(async_client, test_frontdesk):
    """Frontdesk login token'i."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "frontdesk@test.com", "password": "Front123!"}
    )
    return response.json()["access_token"]


@pytest.fixture
async def room_type_db(db: AsyncSession):
    """Test oda tipi."""
    rt = RoomType(
        code="DBL",
        name="Double Room",
        description="Standard double room",
        max_guests=2,
        default_rate=150.00,
        is_active=True
    )
    db.add(rt)
    await db.commit()
    await db.refresh(rt)
    return rt


@pytest.fixture
async def room_db(db: AsyncSession, room_type_db):
    """Test odasi."""
    room = Room(
        room_number="101",
        floor=1,
        room_type_id=room_type_db.id,
        status="clean",
        is_active=True
    )
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


@pytest.fixture
async def guest_db(db: AsyncSession):
    """Test misafiri."""
    guest = Guest(
        first_name="Mehmet",
        last_name="Demir",
        email="mehmet@test.com",
        phone="+905551112233",
        is_vip=False
    )
    db.add(guest)
    await db.commit()
    await db.refresh(guest)
    return guest


@pytest.fixture
async def reservation_db(db: AsyncSession, guest_db, room_type_db, room_db):
    """Test rezervasyonu."""
    check_in = date.today() + timedelta(days=7)
    check_out = date.today() + timedelta(days=10)
    res = Reservation(
        reservation_number=f"RES-{check_in.strftime('%y%m%d')}-0001",
        guest_id=guest_db.id,
        check_in=check_in,
        check_out=check_out,
        adults=2,
        room_type_id=room_type_db.id,
        assigned_room_id=room_db.id,
    )
    db.add(res)
    await db.commit()
    await db.refresh(res)
    return res


@pytest.fixture
async def trace_db(db: AsyncSession, reservation_db):
    """Test trace kaydi."""
    trace = Trace(
        reservation_id=reservation_db.id,
        department="housekeeping",
        subject="Extra towel",
        description="Guest requested extra towels",
        priority="normal",
        status="open",
    )
    db.add(trace)
    await db.commit()
    await db.refresh(trace)
    return trace


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


# ── DeepSeek modül testleri için köprü fixture'lar ──
# Faz 3-4 testleri 'client' + '*_headers' isimlerini bekliyor; conftest async_client +
# token üretiyordu. Aşağıdaki fixture'lar ikisini birbirine bağlar.

@pytest.fixture
async def client(async_client):
    """Faz 3-4 testleri 'client' adını kullanıyor → async_client takma adı."""
    return async_client


@pytest.fixture
async def manager_token(async_client, test_manager):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "manager@test.com", "password": "Manager123!"}
    )
    return response.json()["access_token"]


@pytest.fixture
async def manager_headers(manager_token):
    return {"Authorization": f"Bearer {manager_token}"}


@pytest.fixture
async def superadmin_headers(superadmin_token):
    return {"Authorization": f"Bearer {superadmin_token}"}


@pytest.fixture
async def frontdesk_headers(frontdesk_token):
    return {"Authorization": f"Bearer {frontdesk_token}"}


# ── Groups & Maintenance entity fixture'ları (bu testler kendi fixture'ını tanımlamıyor) ──
from uuid import uuid4 as _uuid4


@pytest.fixture
async def groups_fixture(async_client, manager_headers, room_type_db):
    """Test grubu (master folio ile) + kullanılabilir room_type_id."""
    response = await async_client.post(
        "/api/v1/groups",
        json={
            "name": "Test Group",
            "block_start_date": "2026-07-01",
            "block_end_date": "2026-07-05",
            "pax_count": 30,
            "discount_rate": 10.0,
        },
        headers=manager_headers,
    )
    assert response.status_code == 201, response.text
    return {"group_id": response.json()["id"], "room_type_id": str(room_type_db.id)}


@pytest.fixture
async def assets_fixture(async_client, manager_headers):
    """Test varlığı (category=Electrical — test_get_asset bunu doğruluyor)."""
    response = await async_client.post(
        "/api/v1/maintenance/assets",
        json={
            "name": "Test Asset",
            "category": "Electrical",
            "location": "Room 202",
            "purchase_date": "2023-01-15",
        },
        headers=manager_headers,
    )
    assert response.status_code == 201, response.text
    return {"asset_id": response.json()["id"]}


@pytest.fixture
async def work_order_fixture(async_client, manager_headers):
    """Test iş emri."""
    response = await async_client.post(
        "/api/v1/maintenance/work-orders",
        json={
            "room_id": str(_uuid4()),
            "category": "Plumbing",
            "priority": "normal",
            "description": "Test work order",
            "estimated_hours": 1,
        },
        headers=manager_headers,
    )
    assert response.status_code == 201, response.text
    return {"work_order_id": response.json()["id"]}


# NOT: Audit middleware prod AsyncSessionLocal kullanmaya devam ediyor (test.db'ye
# DOKUNMAZ). Böylece request'in paylaşılan test session'ı ile aynı SQLite dosyasına
# ikinci eşzamanlı yazıcı olmaz → kilit/deadlock riski ortadan kalkar. Audit'in
# "no such table: audit_logs" uyarısı zararsızdır (audit.py try/except ile yakalar).


@pytest.fixture
async def user_db(db: AsyncSession):
    """Genel test kullanıcısı (test_chain property-user atamaları için)."""
    user = User(
        email="staff@test.com",
        hashed_password=get_password_hash("Staff123!"),
        full_name="Test Staff",
        role="frontdesk",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def stay_db(db: AsyncSession, reservation_db, room_db, guest_db):
    """Test konaklaması (mobile check-in EGM/NFC testleri için)."""
    stay = Stay(
        reservation_id=reservation_db.id,
        room_id=room_db.id,
        guest_id=guest_db.id,
        pax_count=2,
        is_checked_in=True,
    )
    db.add(stay)
    await db.commit()
    await db.refresh(stay)
    return stay


@pytest.fixture
async def rate_plan_db(db: AsyncSession, room_type_db):
    """Test rate plan (reservations testleri için)."""
    rp = RatePlan(
        code="BAR",
        name="Best Available Rate",
        room_type_id=room_type_db.id,
        base_rate=150.00,
        is_active=True,
    )
    db.add(rp)
    await db.commit()
    await db.refresh(rp)
    return rp


@pytest.fixture
async def async_client2() -> AsyncGenerator[AsyncClient, None]:
    """İkinci bağımsız test client'ı (RBAC karşılaştırma testleri için)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(autouse=True)
def _shared_db_session(db):
    """Endpoint'ler test 'db' session'ını paylaşsın: endpoint yazıları (örn. housekeeping
    oda durumu) test sorgularında anında görünür ve test.db'ye tek session yazar.
    Default override_get_db (ayrı session) fallback olarak geri yüklenir."""
    async def _override():
        yield db
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def test_housekeeping(db: AsyncSession):
    """Test housekeeping kullanıcısı."""
    user = User(
        email="housekeeping@test.com",
        hashed_password=get_password_hash("House123!"),
        full_name="Test Housekeeping",
        role="housekeeping",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def housekeeping_token(async_client, test_housekeeping):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "housekeeping@test.com", "password": "House123!"},
    )
    return response.json()["access_token"]
