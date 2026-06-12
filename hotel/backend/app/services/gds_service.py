"""
GDS Integration servisi: Kanal yönetimi, rezervasyon senkronizasyonu, rate mapping.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.models.gds import GDSChannel, GDSReservation, GDSRateMapping, GDSSyncLog
from app.schemas.gds import (
    GDSChannelCreate,
    GDSChannelUpdate,
    GDSReservationSync,
    GDSReservationUpdate,
    GDSRateMappingCreate,
    GDSRateMappingUpdate,
)


class GDSService:
    """GDS entegrasyon iş mantığı."""

    # ── Channel ──

    @staticmethod
    async def create_channel(db: AsyncSession, data: GDSChannelCreate, current_user: dict) -> GDSChannel:
        channel = GDSChannel(
            code=data.code,
            name=data.name,
            provider=data.provider,
            config=data.config,
            supported_actions=data.supported_actions,
            notes=data.notes,
            created_by=current_user.get("user_id"),
        )
        db.add(channel)
        await db.commit()
        await db.refresh(channel)
        return channel

    @staticmethod
    async def get_channel(db: AsyncSession, channel_id: UUID) -> Optional[GDSChannel]:
        stmt = select(GDSChannel).where(GDSChannel.id == channel_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_channel(db: AsyncSession, channel_id: UUID, data: GDSChannelUpdate, current_user: dict) -> Optional[GDSChannel]:
        channel = await GDSService.get_channel(db, channel_id)
        if not channel:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(channel, field, value)
        channel.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(channel)
        return channel

    @staticmethod
    async def list_channels(db: AsyncSession, provider: Optional[str] = None, is_active: Optional[bool] = None) -> list[GDSChannel]:
        stmt = select(GDSChannel)
        if provider:
            stmt = stmt.where(GDSChannel.provider == provider)
        if is_active is not None:
            stmt = stmt.where(GDSChannel.is_active == is_active)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Reservation ──

    @staticmethod
    async def sync_reservation(db: AsyncSession, data: GDSReservationSync, current_user: dict) -> GDSReservation:
        """GDS'den gelen rezervasyonu sisteme senkronize et."""
        reservation = GDSReservation(
            channel_id=data.channel_id,
            gds_reservation_id=data.gds_reservation_id,
            guest_name=data.guest_name,
            guest_email=data.guest_email,
            check_in=data.check_in,
            check_out=data.check_out,
            adults=data.adults,
            children=data.children,
            room_type_code=data.room_type_code,
            rate_plan_code=data.rate_plan_code,
            total_amount=data.total_amount,
            currency=data.currency,
            raw_data=data.raw_data,
            status="pending",
            last_sync_at=datetime.now(),
            created_by=current_user.get("user_id"),
        )
        db.add(reservation)

        # Sync log'u kaydet
        sync_log = GDSSyncLog(
            channel_id=data.channel_id,
            action="book",
            status="success",
            request_data=data.model_dump(),
            performed_by=current_user.get("user_id"),
            created_by=current_user.get("user_id"),
        )
        db.add(sync_log)

        await db.commit()
        await db.refresh(reservation)
        return reservation

    @staticmethod
    async def update_reservation(db: AsyncSession, reservation_id: UUID, data: GDSReservationUpdate, current_user: dict) -> Optional[GDSReservation]:
        stmt = select(GDSReservation).where(GDSReservation.id == reservation_id)
        result = await db.execute(stmt)
        reservation = result.scalar_one_or_none()
        if not reservation:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(reservation, field, value)
        if data.status in ("synced", "cancelled", "modified"):
            reservation.last_sync_at = datetime.now()
        reservation.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(reservation)
        return reservation

    @staticmethod
    async def list_reservations(
        db: AsyncSession,
        channel_id: Optional[UUID] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> list[GDSReservation]:
        stmt = select(GDSReservation)
        conditions = []
        if channel_id:
            conditions.append(GDSReservation.channel_id == channel_id)
        if status:
            conditions.append(GDSReservation.status == status)
        if date_from:
            conditions.append(GDSReservation.check_in >= date_from)
        if date_to:
            conditions.append(GDSReservation.check_out <= date_to)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_reservation(db: AsyncSession, reservation_id: UUID) -> Optional[GDSReservation]:
        stmt = select(GDSReservation).where(GDSReservation.id == reservation_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    # ── Rate Mapping ──

    @staticmethod
    async def create_rate_mapping(db: AsyncSession, data: GDSRateMappingCreate, current_user: dict) -> GDSRateMapping:
        mapping = GDSRateMapping(
            channel_id=data.channel_id,
            gds_room_type_code=data.gds_room_type_code,
            gds_rate_plan_code=data.gds_rate_plan_code,
            hotel_room_type_id=data.hotel_room_type_id,
            hotel_rate_plan_id=data.hotel_rate_plan_id,
            markup_percentage=data.markup_percentage,
            created_by=current_user.get("user_id"),
        )
        db.add(mapping)
        await db.commit()
        await db.refresh(mapping)
        return mapping

    @staticmethod
    async def update_rate_mapping(db: AsyncSession, mapping_id: UUID, data: GDSRateMappingUpdate, current_user: dict) -> Optional[GDSRateMapping]:
        stmt = select(GDSRateMapping).where(GDSRateMapping.id == mapping_id)
        result = await db.execute(stmt)
        mapping = result.scalar_one_or_none()
        if not mapping:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(mapping, field, value)
        mapping.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(mapping)
        return mapping

    @staticmethod
    async def list_rate_mappings(db: AsyncSession, channel_id: Optional[UUID] = None) -> list[GDSRateMapping]:
        stmt = select(GDSRateMapping)
        if channel_id:
            stmt = stmt.where(GDSRateMapping.channel_id == channel_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Sync Log ──

    @staticmethod
    async def list_sync_logs(
        db: AsyncSession,
        channel_id: Optional[UUID] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[GDSSyncLog]:
        stmt = select(GDSSyncLog)
        conditions = []
        if channel_id:
            conditions.append(GDSSyncLog.channel_id == channel_id)
        if action:
            conditions.append(GDSSyncLog.action == action)
        if status:
            conditions.append(GDSSyncLog.status == status)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(GDSSyncLog.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
