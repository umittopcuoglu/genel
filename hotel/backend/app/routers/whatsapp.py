"""WhatsApp router'ı: outbound send + Meta webhook (inbound)."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.rbac import require_roles
from app.core.security.param_crypto import decrypt_params
from app.models.integration_setting import IntegrationSetting
from app.models.user import User
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/whatsapp", tags=["WhatsApp"])

GUEST_COMM_ROLES = ["superadmin", "manager", "frontdesk"]


class SendMessageRequest(BaseModel):
    to_phone: str = Field(min_length=5, max_length=20)
    text: str = Field(min_length=1, max_length=4096)
    guest_id: Optional[UUID] = None


@router.post("/send", status_code=status.HTTP_201_CREATED)
async def send_message(
    req: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(GUEST_COMM_ROLES)),
):
    try:
        result = await WhatsAppService.send_message(
            db, req.to_phone, req.text, guest_id=req.guest_id, mock=True
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


# ── Meta WhatsApp webhook (public) ──

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    db: AsyncSession = Depends(get_db),
):
    """Meta'nın webhook doğrulama el sıkışması."""
    res = await db.execute(
        select(IntegrationSetting).where(
            IntegrationSetting.integration_type == "whatsapp",
            IntegrationSetting.enabled.is_(True),
            IntegrationSetting.deleted_at.is_(None),
        )
    )
    row = res.scalars().first()
    expected = ""
    if row:
        params = decrypt_params(row.params_encrypted) or {}
        expected = params.get("verify_token") or params.get("webhook_secret") or ""
    if hub_mode == "subscribe" and hub_verify_token == expected:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Webhook doğrulanamadı")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Meta'dan gelen mesaj/durum webhook'ları."""
    payload = await request.body()

    # İmza doğrulama (opsiyonel — entegrasyonda webhook_secret varsa)
    res = await db.execute(
        select(IntegrationSetting).where(
            IntegrationSetting.integration_type == "whatsapp",
            IntegrationSetting.enabled.is_(True),
            IntegrationSetting.deleted_at.is_(None),
        )
    )
    row = res.scalars().first()
    if row:
        params = decrypt_params(row.params_encrypted) or {}
        secret = params.get("webhook_secret")
        if secret and x_hub_signature_256:
            if not WhatsAppService.verify_webhook_signature(secret, payload, x_hub_signature_256):
                raise HTTPException(status_code=403, detail="İmza geçersiz")

    data = await request.json()
    results = []
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []) or []:
                r = await WhatsAppService.handle_inbound(db, msg)
                results.append(r)
    return {"processed": len(results), "results": results}
