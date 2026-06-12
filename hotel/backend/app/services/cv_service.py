"""
Computer Vision servisi: Oda denetimi, kusur tespiti, envanter yönetimi.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from random import uniform, randint, choice
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from app.models.cv import CVModel, RoomInspection, InspectionDefect, InventorySnapshot
from app.schemas.cv import (
    CVModelCreate,
    RoomInspectionCreate,
    RoomInspectionUpdate,
    RoomInspectionResult,
    DefectVerify,
)


class CVService:
    """Computer Vision iş mantığı."""

    # ── CV Model ──

    @staticmethod
    async def create_model(db: AsyncSession, data: CVModelCreate, current_user: dict) -> CVModel:
        model = CVModel(
            name=data.name,
            version=data.version,
            model_type=data.model_type,
            framework=data.framework,
            accuracy=data.accuracy,
            model_path=data.model_path,
            config=data.config,
            notes=data.notes,
            created_by=current_user.get("user_id"),
        )
        db.add(model)
        await db.commit()
        await db.refresh(model)
        return model

    @staticmethod
    async def list_models(db: AsyncSession, model_type: Optional[str] = None, is_active: Optional[bool] = None) -> list[CVModel]:
        stmt = select(CVModel)
        conditions = []
        if model_type:
            conditions.append(CVModel.model_type == model_type)
        if is_active is not None:
            conditions.append(CVModel.is_active == is_active)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Inspection ──

    @staticmethod
    async def create_inspection(db: AsyncSession, data: RoomInspectionCreate, current_user: dict) -> RoomInspection:
        inspection = RoomInspection(
            room_id=data.room_id,
            inspector_id=data.inspector_id,
            cv_model_id=data.cv_model_id,
            inspection_type=data.inspection_type,
            notes=data.notes,
            created_by=current_user.get("user_id"),
        )
        db.add(inspection)
        await db.commit()
        await db.refresh(inspection)
        return inspection

    @staticmethod
    async def get_inspection(db: AsyncSession, inspection_id: UUID) -> Optional[RoomInspection]:
        stmt = select(RoomInspection).where(RoomInspection.id == inspection_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_inspection(db: AsyncSession, inspection_id: UUID, data: RoomInspectionUpdate, current_user: dict) -> Optional[RoomInspection]:
        inspection = await CVService.get_inspection(db, inspection_id)
        if not inspection:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(inspection, field, value)
        inspection.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(inspection)
        return inspection

    @staticmethod
    async def run_inspection(db: AsyncSession, inspection_id: UUID, current_user: dict) -> Optional[RoomInspectionResult]:
        """CV analizini simüle et (mock)."""
        inspection = await CVService.get_inspection(db, inspection_id)
        if not inspection:
            return None

        # Simülasyon: rastgele skor ve kusurlar üret
        score = Decimal(str(round(uniform(60, 100), 2)))
        defect_types = ["dirty_carpet", "broken_lamp", "stained_bedding", "leaky_faucet", "missing_towel", "scratched_furniture", "mold_spot"]
        categories = {"dirty_carpet": "cleanliness", "broken_lamp": "maintenance", "stained_bedding": "cleanliness", "leaky_faucet": "maintenance", "missing_towel": "amenity", "scratched_furniture": "furniture", "mold_spot": "safety"}
        severities = ["critical", "major", "minor", "cosmetic"]
        suggested = {"dirty_carpet": "Halı temizliği planla", "broken_lamp": "Lamba değiştir", "stained_bedding": "Nevresim değiştir", "leaky_faucet": "Musluk contasını değiştir", "missing_towel": "Havlu tamamla", "scratched_furniture": "Mobilya cilası uygula", "mold_spot": "Küf temizliği yap"}

        num_defects = randint(0, 5)
        defects_created = []
        for _ in range(num_defects):
            dt = choice(defect_types)
            defect = InspectionDefect(
                inspection_id=inspection_id,
                defect_type=dt,
                category=categories.get(dt, "cleanliness"),
                severity=choice(severities),
                confidence=Decimal(str(round(uniform(70, 99), 2))),
                position={"x": randint(0, 800), "y": randint(0, 600), "w": randint(50, 200), "h": randint(50, 200)},
                description=f"Tespit: {dt.replace('_', ' ').title()}",
                suggested_action=suggested.get(dt, "Kontrol et"),
                created_by=current_user.get("user_id"),
            )
            db.add(defect)
            defects_created.append(defect)

        # Inventory snapshots
        inventory_items_result = []
        item_types = ["towel", "pillow", "blanket", "hanger", "glass", "remote"]
        for item in item_types:
            expected = randint(2, 6)
            detected = max(0, expected - randint(0, 2))
            snap = InventorySnapshot(
                room_id=inspection.room_id,
                inspection_id=inspection_id,
                item_type=item,
                expected_count=expected,
                detected_count=detected,
                missing_count=expected - detected,
                confidence=Decimal(str(round(uniform(80, 99), 2))),
                created_by=current_user.get("user_id"),
            )
            db.add(snap)
            inventory_items_result.append({
                "item_type": item,
                "expected_count": expected,
                "detected_count": detected,
                "missing_count": expected - detected,
            })

        # Güncelle
        inspection.status = "completed"
        inspection.score = score
        inspection.defects_count = num_defects
        inspection.raw_result = {"model": "yolov8_mock", "inference_time_ms": randint(200, 1500)}
        inspection.completed_at = datetime.now()
        inspection.updated_by = current_user.get("user_id")

        await db.commit()
        await db.refresh(inspection)

        return RoomInspectionResult(
            score=score,
            defects=[{"id": str(d.id), "type": d.defect_type, "severity": d.severity, "confidence": float(d.confidence)} for d in defects_created],
            inventory_items=inventory_items_result,
        )

    @staticmethod
    async def list_inspections(
        db: AsyncSession,
        room_id: Optional[UUID] = None,
        status: Optional[str] = None,
        inspection_type: Optional[str] = None,
    ) -> list[RoomInspection]:
        stmt = select(RoomInspection)
        conditions = []
        if room_id:
            conditions.append(RoomInspection.room_id == room_id)
        if status:
            conditions.append(RoomInspection.status == status)
        if inspection_type:
            conditions.append(RoomInspection.inspection_type == inspection_type)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(RoomInspection.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    # ── Defects ──

    @staticmethod
    async def list_defects(db: AsyncSession, inspection_id: UUID) -> list[InspectionDefect]:
        stmt = select(InspectionDefect).where(InspectionDefect.inspection_id == inspection_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def verify_defect(db: AsyncSession, defect_id: UUID, data: DefectVerify, current_user: dict) -> Optional[InspectionDefect]:
        stmt = select(InspectionDefect).where(InspectionDefect.id == defect_id)
        result = await db.execute(stmt)
        defect = result.scalar_one_or_none()
        if not defect:
            return None
        defect.is_verified = data.is_verified
        defect.verified_by = current_user.get("user_id")
        defect.verified_at = datetime.now()
        defect.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(defect)
        return defect

    # ── Inventory ──

    @staticmethod
    async def list_inventory(db: AsyncSession, inspection_id: UUID) -> list[InventorySnapshot]:
        stmt = select(InventorySnapshot).where(InventorySnapshot.inspection_id == inspection_id)
        result = await db.execute(stmt)
        return result.scalars().all()
