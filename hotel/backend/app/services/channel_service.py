from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.channel import Channel
from app.models.channel_mapping import ChannelMapping
from app.models.overbooking_rule import OverbookingRule


class ChannelService:
    @staticmethod
    async def get_channel(channel_id: UUID, db: AsyncSession) -> Channel | None:
        result = await db.execute(select(Channel).where(Channel.id == channel_id))
        return result.scalars().first()

    @staticmethod
    async def list_active_channels(db: AsyncSession) -> list[Channel]:
        result = await db.execute(
            select(Channel).where(Channel.enabled == True, Channel.deleted_at == None)
        )
        return result.scalars().all()

    @staticmethod
    async def get_room_mapping(
        channel_id: UUID, external_room_id: str, db: AsyncSession
    ) -> ChannelMapping | None:
        result = await db.execute(
            select(ChannelMapping).where(
                ChannelMapping.channel_id == channel_id,
                ChannelMapping.external_room_id == external_room_id,
            )
        )
        return result.scalars().first()

    @staticmethod
    async def get_overbooking_rule(
        room_type_id: UUID | None, channel_id: UUID | None, db: AsyncSession
    ) -> OverbookingRule | None:
        query = select(OverbookingRule).where(OverbookingRule.enabled == True)
        if room_type_id:
            query = query.where(OverbookingRule.room_type_id == room_type_id)
        if channel_id:
            query = query.where(OverbookingRule.channel_id == channel_id)
        result = await db.execute(query)
        return result.scalars().first()
