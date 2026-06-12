from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from app.models.groups import Group, RoomBlock, Event, EventResource, GroupRoomingList, Venue
from app.models.finance import Folio, FolioStatus
from app.models.front_office import Reservation, ReservationStatus
from app.schemas.groups import (
    GroupCreate,
    RoomBlockCreate,
    EventCreate,
    GroupRoomingListCreate,
)


class GroupsService:
    @staticmethod
    async def create_group(db: AsyncSession, group_data: GroupCreate, current_user: dict) -> Group:
        """Yeni grup oluştur ve master folio'yu otomatik oluştur."""
        # Create group
        group = Group(
            name=group_data.name,
            agency_id=group_data.agency_id,
            contract_number=group_data.contract_number,
            block_start_date=group_data.block_start_date,
            block_end_date=group_data.block_end_date,
            pax_count=group_data.pax_count,
            discount_rate=group_data.discount_rate or Decimal("0"),
            notes=group_data.notes,
            created_by=current_user.get("user_id"),
        )
        db.add(group)
        await db.flush()

        # Create master folio for group
        master_folio = Folio(
            reservation_id=None,
            guest_id=None,
            status="open",
            total=Decimal("0"),
            balance=Decimal("0"),
            created_by=current_user.get("user_id"),
        )
        db.add(master_folio)
        await db.flush()

        group.group_folio_id = master_folio.id
        await db.commit()
        # İlişkileri (room_blocks/events/rooming_list) eager-load ederek dön
        return await GroupsService.get_group(db, group.id)

    @staticmethod
    async def get_group(db: AsyncSession, group_id: UUID) -> Group:
        """Grup detaylarını getir (relationships dahil)."""
        stmt = select(Group).where(Group.id == group_id)
        result = await db.execute(stmt)
        group = result.scalar_one_or_none()
        return group

    @staticmethod
    async def list_groups(db: AsyncSession, status: str = None) -> list[Group]:
        """Grupları listele (duruma göre filter)."""
        stmt = select(Group)
        if status:
            stmt = stmt.where(Group.status == status)
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def update_group_status(
        db: AsyncSession, group_id: UUID, new_status: str, current_user: dict
    ) -> Group | None:
        """Grup durumunu güncelle (transition validation)."""
        group = await GroupsService.get_group(db, group_id)
        if not group:
            return None

        # Validate transition
        valid_transitions = {
            "inquiry": ["confirmed", "cancelled"],
            "confirmed": ["completed", "cancelled"],
            "completed": ["cancelled"],
            "cancelled": [],
        }

        if new_status not in valid_transitions.get(group.status, []):
            raise ValueError(f"Geçersiz durum geçişi: {group.status} → {new_status}")

        # If confirming, check room_blocks have qty_confirmed
        if new_status == "confirmed":
            stmt = select(RoomBlock).where(RoomBlock.group_id == group_id)
            result = await db.execute(stmt)
            blocks = result.scalars().all()
            for block in blocks:
                if block.qty_confirmed < block.qty_required:
                    raise ValueError(
                        f"Blok {block.id}: talep edilen {block.qty_required}, "
                        f"onaylanan {block.qty_confirmed} oda yetersiz (INSUFFICIENT_INVENTORY)"
                    )

        group.status = new_status
        group.updated_by = current_user.get("user_id")
        await db.commit()
        return await GroupsService.get_group(db, group_id)

    @staticmethod
    async def create_room_block(
        db: AsyncSession, group_id: UUID, block_data: RoomBlockCreate, current_user: dict
    ) -> RoomBlock | None:
        """Grup için oda bloku ekle."""
        group = await GroupsService.get_group(db, group_id)
        if not group:
            return None

        block = RoomBlock(
            group_id=group_id,
            room_type_id=block_data.room_type_id,
            qty_required=block_data.qty_required,
            qty_confirmed=block_data.qty_confirmed,
            pickup_date=block_data.pickup_date,
            release_date=block_data.release_date,
            status="pending",
            created_by=current_user.get("user_id"),
        )
        db.add(block)
        await db.commit()
        await db.refresh(block)
        return block

    @staticmethod
    async def release_room_block(
        db: AsyncSession, group_id: UUID, block_id: UUID, current_user: dict
    ) -> RoomBlock | None:
        """Oda bloğunu serbest bırak (release status)."""
        stmt = select(RoomBlock).where(
            and_(RoomBlock.id == block_id, RoomBlock.group_id == group_id)
        )
        result = await db.execute(stmt)
        block = result.scalar_one_or_none()
        if not block:
            return None

        block.status = "released"
        block.updated_by = current_user.get("user_id")
        await db.commit()
        await db.refresh(block)
        return block

    @staticmethod
    async def create_event(
        db: AsyncSession, group_id: UUID, event_data: EventCreate, current_user: dict
    ) -> Event | None:
        """Grup için etkinlik oluştur."""
        group = await GroupsService.get_group(db, group_id)
        if not group:
            return None

        event = Event(
            group_id=group_id,
            title=event_data.title,
            event_type=event_data.event_type,
            venue_id=event_data.venue_id,
            capacity_required=event_data.capacity_required,
            setup_type=event_data.setup_type,
            start_datetime=event_data.start_datetime,
            end_datetime=event_data.end_datetime,
            catering_required=event_data.catering_required,
            notes=event_data.notes,
            created_by=current_user.get("user_id"),
        )
        db.add(event)
        await db.commit()
        # resources ilişkisini eager-load ederek dön (Pydantic MissingGreenlet önle)
        stmt = select(Event).where(Event.id == event.id)
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def import_rooming_list(
        db: AsyncSession,
        group_id: UUID,
        rooming_list: list[GroupRoomingListCreate],
        current_user: dict,
    ) -> int | None:
        """Toplu rooming list import."""
        group = await GroupsService.get_group(db, group_id)
        if not group:
            return None

        imported_count = 0
        for item in rooming_list:
            rooming_item = GroupRoomingList(
                group_id=group_id,
                guest_name=item.guest_name,
                guest_email=item.guest_email,
                guest_phone=item.guest_phone,
                room_type_requested=item.room_type_requested,
                checkin_date=item.checkin_date,
                checkout_date=item.checkout_date,
                status="pending",
                created_by=current_user.get("user_id"),
            )
            db.add(rooming_item)
            imported_count += 1

        await db.commit()
        return imported_count

    @staticmethod
    async def get_rooming_list(db: AsyncSession, group_id: UUID) -> list[GroupRoomingList]:
        """Grubun rooming list'ini getir."""
        stmt = select(GroupRoomingList).where(GroupRoomingList.group_id == group_id)
        result = await db.execute(stmt)
        return result.scalars().all()
