"""
WebSocket endpoint'leri.
"""
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.core.auth import decode_access_token
from app.ws.manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()


async def _verify_token(token: str) -> dict | None:
    """JWT token doğrula, payload döndür."""
    try:
        payload = decode_access_token(token)
        return payload
    except Exception:
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    token: str = Query(...),
):
    """Ana WebSocket bağlantısı — tüm roller."""
    payload = await _verify_token(token)
    if not payload:
        await ws.close(code=1008, reason="Geçersiz token")
        return

    user_id = payload.get("sub", "unknown")
    role = payload.get("role", "guest")

    await manager.connect(ws, user_id, role)
    await ws.send_text(json.dumps({"type": "connected", "user_id": user_id, "role": role}))

    try:
        while True:
            data = await ws.receive_text()
            # İstemciden gelen mesajları logla (ileride işlenebilir)
            logger.debug("WS mesajı [%s]: %s", user_id, data[:200])
    except WebSocketDisconnect:
        await manager.disconnect(ws)
    except Exception as e:
        logger.warning("WS hatası [%s]: %s", user_id, e)
        await manager.disconnect(ws)


@router.websocket("/ws/housekeeping")
async def housekeeping_ws(
    ws: WebSocket,
    token: str = Query(...),
):
    """Housekeeping WebSocket — sadece housekeeping/manager/superadmin."""
    payload = await _verify_token(token)
    if not payload:
        await ws.close(code=1008, reason="Geçersiz token")
        return

    role = payload.get("role", "guest")
    if role not in ("housekeeping", "manager", "superadmin"):
        await ws.close(code=1008, reason="Bu WebSocket'e erişim izniniz yok")
        return

    user_id = payload.get("sub", "unknown")
    await manager.connect(ws, user_id, role)
    await ws.send_text(json.dumps({"type": "connected", "user_id": user_id, "role": role}))

    try:
        while True:
            data = await ws.receive_text()
            logger.debug("HK WS mesajı [%s]: %s", user_id, data[:200])
    except WebSocketDisconnect:
        await manager.disconnect(ws)
    except Exception as e:
        logger.warning("HK WS hatası [%s]: %s", user_id, e)
        await manager.disconnect(ws)
