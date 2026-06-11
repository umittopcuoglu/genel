from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.channel import Channel
from app.models.channel_mapping import ChannelMapping
from app.models.overbooking_rule import OverbookingRule
from app.models.channel_sync_log import ChannelSyncLog
from app.services.channel_service import ChannelService


router = APIRouter(prefix="/channels", tags=["Channels"])


class ChannelCreateRequest(BaseModel):
    name: str
    channel_type: str
    credentials: str
    api_base_url: str | None = None


class ChannelResponse(BaseModel):
    id: UUID
    name: str
    channel_type: str
    enabled: bool
    last_sync_at: str | None = None


@router.post("")
async def create_channel(
    req: ChannelCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChannelResponse:
    if current_user.role not in ["manager", "superadmin"]:
        raise HTTPException(status_code=403)

    channel = Channel(
        name=req.name,
        channel_type=req.channel_type,
        credentials_encrypted=req.credentials,
        api_base_url=req.api_base_url,
        enabled=True,
        created_by=current_user.id,
    )
    db.add(channel)
    await db.commit()

    return ChannelResponse(
        id=channel.id,
        name=channel.name,
        channel_type=channel.channel_type,
        enabled=channel.enabled,
    )


@router.get("")
async def list_channels(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChannelResponse]:
    channels = await ChannelService.list_active_channels(db)
    return [
        ChannelResponse(
            id=c.id,
            name=c.name,
            channel_type=c.channel_type,
            enabled=c.enabled,
            last_sync_at=c.last_sync_at.isoformat() if c.last_sync_at else None,
        )
        for c in channels
    ]


@router.get("/{channel_id}")
async def get_channel(
    channel_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChannelResponse:
    channel = await ChannelService.get_channel(channel_id, db)
    if not channel:
        raise HTTPException(status_code=404)
    return ChannelResponse(
        id=channel.id,
        name=channel.name,
        channel_type=channel.channel_type,
        enabled=channel.enabled,
    )
