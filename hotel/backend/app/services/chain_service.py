"""
Chain servisi: Zincir/mülk CRUD, PropertyUser yönetimi, sync log.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from random import uniform, randint
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.models.chain import Chain, Property, PropertySyncLog, ConsolidatedReport, PropertyUser
from app.schemas.chain import (
    ChainCreate,
    ChainUpdate,
    PropertyCreate,
    PropertyUpdate,
    PropertyUserCreate,
    PropertyUserUpdate,
    ConsolidatedReportGenerate,
)


class ChainService:
    """Çok-mülk yönetimi iş mantığı."""

    # ── Chain ──

    @staticmethod
    async def create_chain(db: AsyncSession, data: ChainCreate, current_user: dict) -> Chain:
        chain = Chain(
            name=data.name,
            code=data.code,
            description=data.description,
            logo_url=data.logo_url,
            website=data.website,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
            config=data.config,
            created_by=current_user.get("user_id"),
        )
        db.add(chain)
        await db.commit()
        await db.refresh(chain)
        return chain

    @staticmethod
    async def get_chain(db: AsyncSession, chain_id: UUID) -> Optional[Chain]:
        stmt = select(Chain).where(Chain.id == chain_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_chain(db: AsyncSession, chain_id: UUID, data: ChainUpdate, current_user: dict) -> Optional[Chain]:
        chain = await ChainService.get_chain(db, chain_id)
        if not chain:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(chain, field, value)
        chain.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(chain)
        return chain

    @staticmethod
    async def list_chains(db: AsyncSession, is_active: Optional[bool] = None) -> list[Chain]:
        stmt = select(Chain)
        if is_active is not None:
            stmt = stmt.where(Chain.is_active == is_active)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Property ──

    @staticmethod
    async def create_property(db: AsyncSession, data: PropertyCreate, current_user: dict) -> Property:
        property = Property(
            chain_id=data.chain_id,
            name=data.name,
            code=data.code,
            property_type=data.property_type,
            address=data.address,
            city=data.city,
            country=data.country,
            currency=data.currency,
            timezone=data.timezone,
            star_rating=data.star_rating,
            total_rooms=data.total_rooms,
            config=data.config,
            notes=data.notes,
            created_by=current_user.get("user_id"),
        )
        db.add(property)
        await db.commit()
        await db.refresh(property)
        return property

    @staticmethod
    async def get_property(db: AsyncSession, property_id: UUID) -> Optional[Property]:
        stmt = select(Property).where(Property.id == property_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_property(db: AsyncSession, property_id: UUID, data: PropertyUpdate, current_user: dict) -> Optional[Property]:
        property = await ChainService.get_property(db, property_id)
        if not property:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(property, field, value)
        property.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(property)
        return property

    @staticmethod
    async def list_properties(db: AsyncSession, chain_id: Optional[UUID] = None, city: Optional[str] = None) -> list[Property]:
        stmt = select(Property)
        conditions = []
        if chain_id:
            conditions.append(Property.chain_id == chain_id)
        if city:
            conditions.append(Property.city == city)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── PropertyUser ──

    @staticmethod
    async def create_property_user(db: AsyncSession, data: PropertyUserCreate, current_user: dict) -> PropertyUser:
        pu = PropertyUser(
            property_id=data.property_id,
            user_id=data.user_id,
            role=data.role,
            created_by=current_user.get("user_id"),
        )
        db.add(pu)
        await db.commit()
        await db.refresh(pu)
        return pu

    @staticmethod
    async def update_property_user(db: AsyncSession, pu_id: UUID, data: PropertyUserUpdate, current_user: dict) -> Optional[PropertyUser]:
        stmt = select(PropertyUser).where(PropertyUser.id == pu_id)
        result = await db.execute(stmt)
        pu = result.scalar_one_or_none()
        if not pu:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pu, field, value)
        pu.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(pu)
        return pu

    @staticmethod
    async def list_property_users(db: AsyncSession, property_id: Optional[UUID] = None) -> list[PropertyUser]:
        stmt = select(PropertyUser)
        if property_id:
            stmt = stmt.where(PropertyUser.property_id == property_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Sync Log ──

    @staticmethod
    async def list_sync_logs(db: AsyncSession, property_id: Optional[UUID] = None, limit: int = 50) -> list[PropertySyncLog]:
        stmt = select(PropertySyncLog)
        if property_id:
            stmt = stmt.where(PropertySyncLog.property_id == property_id)
        stmt = stmt.order_by(PropertySyncLog.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Consolidated Report ──

    @staticmethod
    async def generate_report(db: AsyncSession, data: ConsolidatedReportGenerate, current_user: dict) -> ConsolidatedReport:
        """Konsolide rapor oluştur (mock KPI)."""
        report_date = data.report_date or date.today()
        period_end = data.period_end or report_date
        period_start = data.period_start or date(report_date.year, report_date.month, 1)

        report = ConsolidatedReport(
            chain_id=data.chain_id,
            report_type=data.report_type,
            report_date=report_date,
            period_start=period_start,
            period_end=period_end,
            total_revenue=Decimal(str(round(uniform(100000, 500000), 2))),
            total_occupancy=Decimal(str(round(uniform(60, 95), 2))),
            total_rooms_sold=randint(500, 2000),
            total_available_rooms=randint(800, 2500),
            avg_daily_rate=Decimal(str(round(uniform(120, 350), 2))),
            revpar=Decimal(str(round(uniform(80, 280), 2))),
            data={"currency": "TRY", "properties_count": randint(3, 10)},
            generated_at=datetime.now(),
            created_by=current_user.get("user_id"),
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
        return report

    @staticmethod
    async def list_reports(db: AsyncSession, chain_id: Optional[UUID] = None, report_type: Optional[str] = None, limit: int = 20) -> list[ConsolidatedReport]:
        stmt = select(ConsolidatedReport)
        conditions = []
        if chain_id:
            conditions.append(ConsolidatedReport.chain_id == chain_id)
        if report_type:
            conditions.append(ConsolidatedReport.report_type == report_type)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(ConsolidatedReport.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
