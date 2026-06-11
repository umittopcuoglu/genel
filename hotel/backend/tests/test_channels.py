import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.base import Base
from app.models.channel import Channel
from app.models.channel_mapping import ChannelMapping
from app.models.overbooking_rule import OverbookingRule
from app.models.channel_sync_log import ChannelSyncLog
from app.services.channel_service import ChannelService


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_create_channel(db_session):
    channel = Channel(
        name="booking_com",
        channel_type="ota",
        credentials_encrypted="encrypted_key",
        enabled=True,
        created_by=uuid4(),
    )
    db_session.add(channel)
    await db_session.commit()

    assert channel.id is not None
    assert channel.name == "booking_com"
    assert channel.enabled is True


@pytest.mark.asyncio
async def test_list_active_channels(db_session):
    channel1 = Channel(
        name="booking_com",
        channel_type="ota",
        credentials_encrypted="key1",
        enabled=True,
        created_by=uuid4(),
    )
    channel2 = Channel(
        name="expedia",
        channel_type="ota",
        credentials_encrypted="key2",
        enabled=False,
        created_by=uuid4(),
    )
    db_session.add(channel1)
    db_session.add(channel2)
    await db_session.commit()

    active_channels = await ChannelService.list_active_channels(db_session)
    assert len(active_channels) == 1
    assert active_channels[0].name == "booking_com"


@pytest.mark.asyncio
async def test_overbooking_rule(db_session):
    rule = OverbookingRule(
        overbooking_percent=5.0,
        enabled=True,
        note="Summer peak season",
        created_by=uuid4(),
    )
    db_session.add(rule)
    await db_session.commit()

    retrieved_rule = await ChannelService.get_overbooking_rule(None, None, db_session)
    assert retrieved_rule is not None
    assert retrieved_rule.overbooking_percent == 5.0


@pytest.mark.asyncio
async def test_channel_sync_log(db_session):
    channel = Channel(
        name="test_channel",
        channel_type="ota",
        credentials_encrypted="key",
        created_by=uuid4(),
    )
    db_session.add(channel)
    await db_session.commit()

    log = ChannelSyncLog(
        channel_id=channel.id,
        sync_type="availability",
        status="success",
        reservations_synced=10,
        rooms_updated=5,
        response_time_ms=250,
        created_by=uuid4(),
    )
    db_session.add(log)
    await db_session.commit()

    assert log.channel_id == channel.id
    assert log.status == "success"
    assert log.reservations_synced == 10
