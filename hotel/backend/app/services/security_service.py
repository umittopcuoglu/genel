"""TASK-017 — Güvenlik & KVKK servis katmanı."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from app.models.security import (
    DoorLock, KeyCard, AccessLog, Incident, KVKKConsent, DataAccessRequest,
)
from app.schemas.security import (
    DoorLockCreate, KeyCardCreate, AccessLogCreate,
    IncidentCreate, KVKKConsentCreate, DataAccessRequestCreate,
)


class SecurityService:
    # ── Door Locks ──
    @staticmethod
    async def create_door_lock(db: AsyncSession, data: DoorLockCreate, current_user: dict) -> DoorLock:
        lock = DoorLock(
            name=data.name, area=data.area, room_id=data.room_id,
            created_by=current_user.get("user_id"),
        )
        db.add(lock)
        await db.commit()
        await db.refresh(lock)
        return lock

    @staticmethod
    async def list_door_locks(db: AsyncSession) -> list[DoorLock]:
        result = await db.execute(select(DoorLock))
        return result.scalars().all()

    # ── Key Cards ──
    @staticmethod
    async def issue_card(db: AsyncSession, data: KeyCardCreate, current_user: dict) -> KeyCard:
        card = KeyCard(
            card_number=data.card_number,
            owner_type=data.owner_type,
            owner_name=data.owner_name,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            reservation_id=data.reservation_id,
            status="active",
            created_by=current_user.get("user_id"),
        )
        db.add(card)
        await db.commit()
        await db.refresh(card)
        return card

    @staticmethod
    async def list_cards(db: AsyncSession) -> list[KeyCard]:
        result = await db.execute(select(KeyCard))
        return result.scalars().all()

    @staticmethod
    async def revoke_card(db: AsyncSession, card_id: UUID, current_user: dict) -> KeyCard | None:
        result = await db.execute(select(KeyCard).where(KeyCard.id == card_id))
        card = result.scalar_one_or_none()
        if not card:
            return None
        card.status = "revoked"
        await db.commit()
        await db.refresh(card)
        return card

    # ── Access Logs ──
    @staticmethod
    async def log_access(db: AsyncSession, data: AccessLogCreate, current_user: dict) -> AccessLog:
        log = AccessLog(
            door_lock_id=data.door_lock_id,
            area=data.area,
            card_number=data.card_number,
            person_name=data.person_name,
            result=data.result,
            accessed_at=datetime.utcnow(),
            created_by=current_user.get("user_id"),
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def list_access_logs(db: AsyncSession, result_filter: str | None = None) -> list[AccessLog]:
        stmt = select(AccessLog)
        if result_filter:
            stmt = stmt.where(AccessLog.result == result_filter)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Incidents ──
    @staticmethod
    async def create_incident(db: AsyncSession, data: IncidentCreate, current_user: dict) -> Incident:
        incident = Incident(
            title=data.title,
            incident_type=data.incident_type,
            severity=data.severity,
            description=data.description,
            status="open",
            reported_at=datetime.utcnow(),
            created_by=current_user.get("user_id"),
        )
        db.add(incident)
        await db.commit()
        await db.refresh(incident)
        return incident

    @staticmethod
    async def list_incidents(db: AsyncSession) -> list[Incident]:
        result = await db.execute(select(Incident))
        return result.scalars().all()

    @staticmethod
    async def update_incident_status(db: AsyncSession, incident_id: UUID, new_status: str, current_user: dict) -> Incident | None:
        result = await db.execute(select(Incident).where(Incident.id == incident_id))
        incident = result.scalar_one_or_none()
        if not incident:
            return None
        incident.status = new_status
        if new_status in ("resolved", "closed"):
            incident.resolved_at = datetime.utcnow()
        await db.commit()
        await db.refresh(incident)
        return incident

    # ── KVKK ──
    @staticmethod
    async def create_consent(db: AsyncSession, data: KVKKConsentCreate, current_user: dict) -> KVKKConsent:
        consent = KVKKConsent(
            guest_id=data.guest_id,
            guest_name=data.guest_name,
            purpose=data.purpose,
            status="granted",
            consent_date=datetime.utcnow(),
            created_by=current_user.get("user_id"),
        )
        db.add(consent)
        await db.commit()
        await db.refresh(consent)
        return consent

    @staticmethod
    async def list_consents(db: AsyncSession) -> list[KVKKConsent]:
        result = await db.execute(select(KVKKConsent))
        return result.scalars().all()

    @staticmethod
    async def withdraw_consent(db: AsyncSession, consent_id: UUID, current_user: dict) -> KVKKConsent | None:
        result = await db.execute(select(KVKKConsent).where(KVKKConsent.id == consent_id))
        consent = result.scalar_one_or_none()
        if not consent:
            return None
        consent.status = "withdrawn"
        consent.withdrawn_at = datetime.utcnow()
        await db.commit()
        await db.refresh(consent)
        return consent

    @staticmethod
    async def create_data_request(db: AsyncSession, data: DataAccessRequestCreate, current_user: dict) -> DataAccessRequest:
        req = DataAccessRequest(
            guest_id=data.guest_id,
            guest_name=data.guest_name,
            request_type=data.request_type,
            status="pending",
            requested_at=datetime.utcnow(),
            notes=data.notes,
            created_by=current_user.get("user_id"),
        )
        db.add(req)
        await db.commit()
        await db.refresh(req)
        return req

    @staticmethod
    async def list_data_requests(db: AsyncSession) -> list[DataAccessRequest]:
        result = await db.execute(select(DataAccessRequest))
        return result.scalars().all()

    @staticmethod
    async def complete_data_request(db: AsyncSession, request_id: UUID, current_user: dict) -> DataAccessRequest | None:
        result = await db.execute(select(DataAccessRequest).where(DataAccessRequest.id == request_id))
        req = result.scalar_one_or_none()
        if not req:
            return None
        req.status = "completed"
        req.completed_at = datetime.utcnow()
        await db.commit()
        await db.refresh(req)
        return req
