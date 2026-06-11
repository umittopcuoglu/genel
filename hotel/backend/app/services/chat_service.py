from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.front_office import Guest


class ChatService:
    @staticmethod
    async def get_or_create_session(guest_id: UUID, db: AsyncSession) -> ChatSession:
        """Aktif oturum al veya yeni oluştur (1 saatlik inaktivite sonrası yeni)."""
        result = await db.execute(
            select(ChatSession)
            .where(
                ChatSession.guest_id == guest_id,
                ChatSession.status == "active",
            )
            .order_by(ChatSession.created_at.desc())
            .limit(1)
        )
        session = result.scalars().first()

        if session:
            delta = (datetime.utcnow() - session.updated_at.replace(tzinfo=None)).total_seconds()
            if delta < 3600:
                return session

        new_session = ChatSession(
            guest_id=guest_id,
            status="active",
            context={},
            created_by=UUID(int=0),
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        return new_session

    @staticmethod
    async def add_message(
        session_id: UUID, role: str, content: str, sentiment: str | None, db: AsyncSession
    ) -> ChatMessage:
        """Oturuma mesaj ekle."""
        message = ChatMessage(
            chat_session_id=session_id,
            role=role,
            content=content,
            sentiment=sentiment,
            created_by=UUID(int=0),
        )
        db.add(message)

        session = await db.get(ChatSession, session_id)
        session.updated_at = datetime.utcnow()
        await db.commit()

        return message

    @staticmethod
    async def get_session_history(session_id: UUID, db: AsyncSession, limit: int = 10) -> list[ChatMessage]:
        """Oturum mesaj tarihçesi."""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))

    @staticmethod
    def detect_sentiment(text: str) -> str:
        """Sentiment tespiti."""
        negative = ["kötü", "sorun", "berbat", "şikayet", "çöktü"]
        positive = ["harika", "mükemmel", "iyi", "beğendim"]

        text_lower = text.lower()
        if any(w in text_lower for w in negative):
            return "negative"
        if any(w in text_lower for w in positive):
            return "positive"
        return "neutral"
