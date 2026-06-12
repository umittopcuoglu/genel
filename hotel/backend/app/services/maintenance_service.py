from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal
from app.models.maintenance import Asset, WorkOrder, PreventiveMaintenance, MaintenanceLog
from app.schemas.maintenance import (
    AssetCreate,
    WorkOrderCreate,
    PreventiveMaintenanceCreate,
    MaintenanceLogCreate,
)


class MaintenanceService:
    @staticmethod
    async def create_asset(db: AsyncSession, asset_data: AssetCreate, current_user: dict) -> Asset:
        """Yeni varlık oluştur."""
        asset = Asset(
            name=asset_data.name,
            category=asset_data.category,
            location=asset_data.location,
            purchase_date=asset_data.purchase_date,
            warranty_end_date=asset_data.warranty_end_date,
            notes=asset_data.notes,
            created_by=current_user.get("user_id"),
        )
        db.add(asset)
        await db.commit()
        await db.refresh(asset)
        return asset

    @staticmethod
    async def get_asset(db: AsyncSession, asset_id: UUID) -> Asset | None:
        """Varlık detaylarını getir."""
        stmt = select(Asset).where(Asset.id == asset_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_assets(db: AsyncSession) -> list[Asset]:
        """Tüm varlıkları listele."""
        stmt = select(Asset)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def create_work_order(db: AsyncSession, order_data: WorkOrderCreate, current_user: dict) -> WorkOrder:
        """Yeni iş emri oluştur."""
        work_order = WorkOrder(
            room_id=order_data.room_id,
            category=order_data.category,
            priority=order_data.priority,
            description=order_data.description,
            status="open",
            estimated_hours=order_data.estimated_hours,
            opened_at=datetime.utcnow(),
            created_by=current_user.get("user_id"),
        )
        db.add(work_order)
        await db.commit()
        await db.refresh(work_order)
        return work_order

    @staticmethod
    async def get_work_order(db: AsyncSession, work_order_id: UUID) -> WorkOrder | None:
        """İş emri detaylarını getir."""
        stmt = select(WorkOrder).where(WorkOrder.id == work_order_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_work_orders(db: AsyncSession, status: str = None) -> list[WorkOrder]:
        """İş emirlerini listele (duruma göre filtrele)."""
        stmt = select(WorkOrder)
        if status:
            stmt = stmt.where(WorkOrder.status == status)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def update_work_order_status(
        db: AsyncSession, work_order_id: UUID, new_status: str, notes: str | None, current_user: dict
    ) -> WorkOrder | None:
        """İş emri durumunu güncelle."""
        work_order = await MaintenanceService.get_work_order(db, work_order_id)
        if not work_order:
            return None

        work_order.status = new_status
        if notes:
            work_order.notes = notes
        if new_status == "completed":
            work_order.completed_at = datetime.utcnow()
        work_order.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(work_order)
        return work_order

    @staticmethod
    async def assign_work_order(
        db: AsyncSession, work_order_id: UUID, assigned_to: UUID, current_user: dict
    ) -> WorkOrder | None:
        """İş emrini personele ata."""
        work_order = await MaintenanceService.get_work_order(db, work_order_id)
        if not work_order:
            return None

        work_order.assigned_to = assigned_to if isinstance(assigned_to, UUID) else UUID(str(assigned_to))
        work_order.assigned_at = datetime.utcnow()
        work_order.status = "assigned"
        work_order.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(work_order)
        return work_order

    @staticmethod
    async def create_preventive_maintenance(
        db: AsyncSession, pm_data: PreventiveMaintenanceCreate, current_user: dict
    ) -> PreventiveMaintenance:
        """Preventif bakım planı oluştur."""
        pm = PreventiveMaintenance(
            asset_id=pm_data.asset_id,
            description=pm_data.description,
            frequency_days=pm_data.frequency_days,
            next_maintenance_date=date.today() + timedelta(days=pm_data.frequency_days),
            created_by=current_user.get("user_id"),
        )
        db.add(pm)
        await db.commit()
        await db.refresh(pm)
        return pm

    @staticmethod
    async def get_due_maintenance(db: AsyncSession) -> list[PreventiveMaintenance]:
        """Vadesi gelen preventif bakımları getir."""
        stmt = select(PreventiveMaintenance).where(
            and_(
                PreventiveMaintenance.next_maintenance_date <= date.today(),
                PreventiveMaintenance.status == "active",
            )
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def create_maintenance_log(
        db: AsyncSession, log_data: MaintenanceLogCreate, current_user: dict
    ) -> MaintenanceLog:
        """Bakım işlemini kaydet."""
        log = MaintenanceLog(
            work_order_id=log_data.work_order_id,
            asset_id=log_data.asset_id,
            performed_by=UUID(current_user.get("user_id")),
            parts_used=log_data.parts_used,
            hours_spent=log_data.hours_spent,
            cost=log_data.cost,
            notes=log_data.notes,
            completed_at=datetime.utcnow(),
            created_by=current_user.get("user_id"),
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def get_work_order_logs(db: AsyncSession, work_order_id: UUID) -> list[MaintenanceLog]:
        """İş emrinin bakım geçmişini getir."""
        stmt = select(MaintenanceLog).where(MaintenanceLog.work_order_id == work_order_id)
        result = await db.execute(stmt)
        return result.scalars().all()
