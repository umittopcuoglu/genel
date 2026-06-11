import pytest
from uuid import uuid4
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.base import Base
from app.models.chart_of_accounts import ChartOfAccount
from app.models.ledger_entry import LedgerEntry
from app.models.front_office import Guest
from app.models.chat_session import ChatSession
from app.services.accounting_service import AccountingService
from app.services.chat_service import ChatService
from app.services.guest_360_service import Guest360Service


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_post_folio_closure(db_session):
    account = ChartOfAccount(
        account_code="610",
        account_name="Oda Geliri",
        account_type="revenue",
        normal_balance="credit",
        balance_sheet_order=1,
        created_by=uuid4(),
    )
    db_session.add(account)

    payment_account = ChartOfAccount(
        account_code="110",
        account_name="Kasa",
        account_type="asset",
        normal_balance="debit",
        balance_sheet_order=1,
        created_by=uuid4(),
    )
    db_session.add(payment_account)
    await db_session.commit()

    result = await AccountingService.post_folio_closure(
        uuid4(), Decimal(1000), db_session
    )

    assert result["amount"] == 1000.0
    assert result["status"] == "draft"


@pytest.mark.asyncio
async def test_chat_sentiment_detection():
    assert ChatService.detect_sentiment("Bu çok kötü") == "negative"
    assert ChatService.detect_sentiment("Harika hizmet") == "positive"
    assert ChatService.detect_sentiment("Orta kalite") == "neutral"


@pytest.mark.asyncio
async def test_get_or_create_session(db_session):
    guest_id = uuid4()

    session1 = await ChatService.get_or_create_session(guest_id, db_session)
    assert session1.guest_id == guest_id
    assert session1.status == "active"

    session2 = await ChatService.get_or_create_session(guest_id, db_session)
    assert session1.id == session2.id


@pytest.mark.asyncio
async def test_chat_add_message(db_session):
    guest_id = uuid4()
    session = await ChatService.get_or_create_session(guest_id, db_session)

    message = await ChatService.add_message(
        session.id, "user", "Merhaba", "neutral", db_session
    )

    assert message.chat_session_id == session.id
    assert message.role == "user"
    assert message.content == "Merhaba"
