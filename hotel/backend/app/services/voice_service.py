"""
Voice Control servisi: Alexa/Google webhook, komut yönetimi, intent eşleme.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from random import uniform, randint, choice
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.models.voice import VoiceIntegration, VoiceCommand, VoiceSession, VoiceInteraction, VoiceIntentsMapping
from app.schemas.voice import (
    VoiceIntegrationCreate,
    VoiceIntegrationUpdate,
    VoiceIntentsMappingCreate,
)


class VoiceService:
    """Sesli kontrol iş mantığı."""

    # ── Integration ──

    @staticmethod
    async def create_integration(db: AsyncSession, data: VoiceIntegrationCreate, current_user: dict) -> VoiceIntegration:
        integration = VoiceIntegration(
            room_id=data.room_id,
            provider=data.provider,
            device_id=data.device_id,
            device_name=data.device_name,
            locale=data.locale,
            config=data.config,
            notes=data.notes,
            created_by=current_user.get("user_id"),
        )
        db.add(integration)
        await db.commit()
        await db.refresh(integration)
        return integration

    @staticmethod
    async def get_integration(db: AsyncSession, integration_id: UUID) -> Optional[VoiceIntegration]:
        stmt = select(VoiceIntegration).where(VoiceIntegration.id == integration_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_integration(db: AsyncSession, integration_id: UUID, data: VoiceIntegrationUpdate, current_user: dict) -> Optional[VoiceIntegration]:
        integration = await VoiceService.get_integration(db, integration_id)
        if not integration:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(integration, field, value)
        integration.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(integration)
        return integration

    @staticmethod
    async def list_integrations(db: AsyncSession, room_id: Optional[UUID] = None, provider: Optional[str] = None) -> list[VoiceIntegration]:
        stmt = select(VoiceIntegration)
        conditions = []
        if room_id:
            conditions.append(VoiceIntegration.room_id == room_id)
        if provider:
            conditions.append(VoiceIntegration.provider == provider)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Webhook Handling (mock) ──

    @staticmethod
    async def handle_alexa_webhook(db: AsyncSession, payload: dict, current_user: dict) -> dict:
        """Alexa skill webhook'unu işle (mock)."""
        request = payload.get("request", {})
        request_type = request.get("type", "LaunchRequest")
        intent_name = request.get("intent", {}).get("name", "") if request_type == "IntentRequest" else ""

        # Session log
        session_info = payload.get("session", {})
        session_id = session_info.get("sessionId", "unknown")
        device_id = session_info.get("user", {}).get("userId", "unknown")

        integration = None
        stmt = select(VoiceIntegration).where(VoiceIntegration.device_id == device_id)
        result = await db.execute(stmt)
        integration = result.scalar_one_or_none()

        if not integration:
            return VoiceService._alexa_response("Cihaz bulunamadı. Lütfen otel resepsiyonu ile iletişime geçin.")

        interaction = VoiceInteraction(
            integration_id=integration.id,
            direction="incoming",
            provider="alexa",
            request_type=request_type,
            raw_request=payload,
            created_by=current_user.get("user_id"),
        )

        # Intent mapping
        response_text = "Komut anlaşılamadı"
        if request_type == "LaunchRequest":
            response_text = "HotelOps sesli asistana hoş geldiniz. Size nasıl yardımcı olabilirim?"
        elif intent_name:
            stmt = select(VoiceIntentsMapping).where(
                VoiceIntentsMapping.provider == "alexa",
                VoiceIntentsMapping.intent_name == intent_name,
                VoiceIntentsMapping.is_active == True,
            )
            result = await db.execute(stmt)
            mapping = result.scalar_one_or_none()
            if mapping:
                response_text = f"{mapping.action} komutu alındı, uygulanıyor..."
            else:
                response_text = f"'{intent_name}' komutu tanınmadı."

            VoiceCommand(
                integration_id=integration.id,
                session_id=session_id,
                intent=intent_name or "unknown",
                raw_text=str(request.get("intent", {}).get("slots", {})),
                confidence=uniform(0.7, 0.99),
                result="success" if mapping else "not_understood",
                response_text=response_text,
                executed_at=datetime.now(),
                performed_by=current_user.get("user_id"),
                created_by=current_user.get("user_id"),
            )

        interaction.raw_response = {"speech": response_text}
        db.add(interaction)
        await db.commit()

        return VoiceService._alexa_response(response_text)

    @staticmethod
    async def handle_google_webhook(db: AsyncSession, payload: dict, current_user: dict) -> dict:
        """Google Actions webhook'unu işle (mock)."""
        inputs = payload.get("inputs", [{}])
        intent_name = inputs[0].get("intent", "") if inputs else ""

        response_text = "Komut anlaşılamadı"
        if not intent_name:
            response_text = "HotelOps sesli asistana hoş geldiniz."
        else:
            stmt = select(VoiceIntentsMapping).where(
                VoiceIntentsMapping.provider == "google_assistant",
                VoiceIntentsMapping.intent_name == intent_name,
                VoiceIntentsMapping.is_active == True,
            )
            result = await db.execute(stmt)
            mapping = result.scalar_one_or_none()
            if mapping:
                response_text = f"{mapping.action} uygulanıyor."
            else:
                response_text = f"'{intent_name}' komutu tanınmadı."

        return {
            "payload": {
                "google": {
                    "expectUserResponse": True,
                    "richResponse": {
                        "items": [{"simpleResponse": {"textToSpeech": response_text}}],
                    },
                }
            }
        }

    @staticmethod
    def _alexa_response(speech_text: str) -> dict:
        return {
            "version": "1.0",
            "response": {
                "outputSpeech": {"type": "PlainText", "text": speech_text},
                "shouldEndSession": False,
            },
        }

    # ── Intents Mapping ──

    @staticmethod
    async def create_intent_mapping(db: AsyncSession, data: VoiceIntentsMappingCreate, current_user: dict) -> VoiceIntentsMapping:
        mapping = VoiceIntentsMapping(
            provider=data.provider,
            intent_name=data.intent_name,
            action=data.action,
            action_params_template=data.action_params_template,
            description=data.description,
            created_by=current_user.get("user_id"),
        )
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        return mapping

    @staticmethod
    async def list_intent_mappings(db: AsyncSession, provider: Optional[str] = None) -> list[VoiceIntentsMapping]:
        stmt = select(VoiceIntentsMapping)
        if provider:
            stmt = stmt.where(VoiceIntentsMapping.provider == provider)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Commands ──

    @staticmethod
    async def list_commands(db: AsyncSession, integration_id: Optional[UUID] = None, limit: int = 50) -> list[VoiceCommand]:
        stmt = select(VoiceCommand)
        if integration_id:
            stmt = stmt.where(VoiceCommand.integration_id == integration_id)
        stmt = stmt.order_by(VoiceCommand.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Sessions ──

    @staticmethod
    async def list_sessions(db: AsyncSession, integration_id: Optional[UUID] = None, limit: int = 20) -> list[VoiceSession]:
        stmt = select(VoiceSession)
        if integration_id:
            stmt = stmt.where(VoiceSession.integration_id == integration_id)
        stmt = stmt.order_by(VoiceSession.started_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Interactions ──

    @staticmethod
    async def list_interactions(db: AsyncSession, integration_id: Optional[UUID] = None, limit: int = 50) -> list[VoiceInteraction]:
        stmt = select(VoiceInteraction)
        if integration_id:
            stmt = stmt.where(VoiceInteraction.integration_id == integration_id)
        stmt = stmt.order_by(VoiceInteraction.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
