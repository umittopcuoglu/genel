import pytest
from uuid import uuid4
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.base import Base
from app.models.loyalty_account import LoyaltyAccount
from app.models.loyalty_transaction import LoyaltyTransaction
from app.models.complaint import Complaint
from app.models.feedback import Feedback
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.custom_report import CustomReport
from app.models.budget import Budget
from app.services.loyalty_service import LoyaltyService


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_earn_loyalty_points(db_session):
    guest_id = uuid4()
    folio_id = uuid4()

    result = await LoyaltyService.earn_points(
        guest_id, Decimal(100), folio_id, db_session
    )

    assert result["points_earned"] == 100
    assert result["new_balance"] == 100


@pytest.mark.asyncio
async def test_redeem_loyalty_points(db_session):
    guest_id = uuid4()
    folio_id = uuid4()

    await LoyaltyService.earn_points(guest_id, Decimal(600), folio_id, db_session)
    result = await LoyaltyService.redeem_points(
        guest_id, 500, "free_night", db_session
    )

    assert result["redeemed_points"] == 500
    assert result["new_balance"] == 100


@pytest.mark.asyncio
async def test_loyalty_tier_multiplier(db_session):
    guest_id = uuid4()
    folio_id = uuid4()

    loyalty = LoyaltyAccount(
        guest_id=guest_id,
        tier="gold",
        tier_since="2026-06-11",
        total_points=0,
        available_points=0,
        created_by=uuid4(),
    )
    db_session.add(loyalty)
    await db_session.commit()

    result = await LoyaltyService.earn_points(
        guest_id, Decimal(100), folio_id, db_session
    )

    assert result["points_earned"] == 110


@pytest.mark.asyncio
async def test_create_complaint(db_session):
    guest_id = uuid4()
    reservation_id = uuid4()

    complaint = Complaint(
        guest_id=guest_id,
        reservation_id=reservation_id,
        title="Kötü hizmet",
        description="Odada sorun vardı",
        complaint_type="room",
        severity="high",
        status="open",
        created_by=uuid4(),
    )
    db_session.add(complaint)
    await db_session.commit()

    assert complaint.id is not None
    assert complaint.status == "open"
    assert complaint.severity == "high"


@pytest.mark.asyncio
async def test_create_feedback(db_session):
    guest_id = uuid4()
    reservation_id = uuid4()

    feedback = Feedback(
        guest_id=guest_id,
        reservation_id=reservation_id,
        rating=5,
        comment="Çok güzel bir otel",
        categories="cleanliness,staff,value_for_money",
        status="new",
        created_by=uuid4(),
    )
    db_session.add(feedback)
    await db_session.commit()

    assert feedback.rating == 5
    assert feedback.status == "new"


@pytest.mark.asyncio
async def test_chat_session_and_messages(db_session):
    guest_id = uuid4()

    session = ChatSession(
        guest_id=guest_id,
        status="active",
        context={},
        created_by=uuid4(),
    )
    db_session.add(session)
    await db_session.commit()

    message = ChatMessage(
        chat_session_id=session.id,
        role="user",
        content="Merhaba",
        created_by=uuid4(),
    )
    db_session.add(message)
    await db_session.commit()

    assert message.chat_session_id == session.id
    assert message.role == "user"


@pytest.mark.asyncio
async def test_custom_report(db_session):
    report = CustomReport(
        name="Monthly Revenue",
        description="Monthly revenue report",
        definition={
            "source": "folios",
            "filters": [{"field": "closed_date", "op": ">=", "value": "2026-06-01"}],
        },
        created_by=uuid4(),
    )
    db_session.add(report)
    await db_session.commit()

    assert report.id is not None
    assert report.name == "Monthly Revenue"


@pytest.mark.asyncio
async def test_budget_variance(db_session):
    budget = Budget(
        department="rooms",
        budget_year=2026,
        budget_month=6,
        budgeted_revenue=Decimal(50000),
        budgeted_expense=Decimal(20000),
        actual_revenue=Decimal(52000),
        actual_expense=Decimal(19000),
        variance_percent=4.0,
        status="actual_calculated",
        created_by=uuid4(),
    )
    db_session.add(budget)
    await db_session.commit()

    assert budget.variance_percent == 4.0
