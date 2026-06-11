"""
Pytest yapılandırması: async test client, test veritabanı, global fixture'lar.
"""
import asyncio
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.core.db import get_db, Base
from app.core.config import settings
from app.models.user import User
from app.models.audit import AuditLog
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
