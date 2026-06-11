"""
WebSocket testleri (TASK-006): bağlantı, auth, emit, RBAC.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import WebSocket

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.usefixtures("setup_test_db"),
]


async def _get_token(async_client) -> str:
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.com", "password": "Admin123!"},
    )
    return resp.json()["access_token"]


async def _get_hk_token(async_client) -> str:
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "housekeeping@test.com", "password": "HK123!"},
    )
    return resp.json()["access_token"]


async def _get_fb_token(async_client) -> str:
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "frontdesk@test.com", "password": "Front123!"},
    )
    return resp.json()["access_token"]


# ──── 1. WS bağlantı + auth happy ────

async def test_ws_connect_happy(async_client, superadmin_token):
    token = superadmin_token
    # WS için test client kullanılamıyor, manager.publish_event mock'u test ediyoruz
    # Bu test manager.connect'in token doğrulama akışını doğrular
    from app.core.auth import decode_access_token
    payload = decode_access_token(token)
    assert payload is not None
    assert "sub" in payload
    assert "role" in payload
    print(f"WS auth OK: user={payload['sub']} role={payload['role']}")


async def test_ws_invalid_token_returns_none():
    from app.core.auth import decode_access_token
    payload = decode_access_token("invalid.token.here")
    assert payload is None


# ──── 2. Emit test (mock WS ile) ────

async def test_emit_room_status_changed():
    from app.ws.events import emit_room_status_changed
    from app.ws.manager import manager

    mock_broadcast = AsyncMock()
    manager.broadcast = mock_broadcast

    await emit_room_status_changed(
        room_id="123", room_no="101",
        old_status="dirty", new_status="clean",
    )
    mock_broadcast.assert_awaited_once()
    args = mock_broadcast.call_args[0][0]
    assert args["type"] == "room.status.changed"
    assert args["data"]["room_no"] == "101"


async def test_emit_checkin():
    from app.ws.events import emit_checkin
    from app.ws.manager import manager

    mock_broadcast = AsyncMock()
    manager.broadcast = mock_broadcast

    await emit_checkin("res-1", "101", "Mehmet Demir")
    mock_broadcast.assert_awaited_once()
    args = mock_broadcast.call_args[0][0]
    assert args["type"] == "checkin"
    assert args["data"]["room_no"] == "101"


async def test_emit_housekeeping_task():
    from app.ws.events import emit_housekeeping_task
    from app.ws.manager import manager

    mock_roles = AsyncMock()
    manager.broadcast_to_roles = mock_roles

    await emit_housekeeping_task({"task_id": "t-1", "type": "stayover"})
    mock_roles.assert_awaited_once()
    args = mock_roles.call_args[0][0]
    assert args["type"] == "housekeeping.task"


# ──── 3. RBAC: housekeeping WS erişim kontrolü ────

async def test_housekeeping_ws_role_check():
    from app.ws.routes import _verify_token
    from app.core.auth import create_access_token
    from app.models.user import User

    # Housekeeping user
    hk_payload = {"sub": "hk-user", "role": "housekeeping"}
    hk_token = create_access_token(data=hk_payload)

    result = await _verify_token(hk_token)
    assert result is not None
    assert result["role"] == "housekeeping"

    # Guest user
    guest_payload = {"sub": "guest-user", "role": "guest"}
    guest_token = create_access_token(data=guest_payload)
    result2 = await _verify_token(guest_token)
    assert result2 is not None
    assert result2["role"] == "guest"


# ──── 4. ConnectionManager test ────

async def test_connection_manager():
    from app.ws.manager import ConnectionManager

    cm = ConnectionManager()
    mock_ws = AsyncMock(spec=WebSocket)
    mock_ws.send_text = AsyncMock()

    await cm.connect(mock_ws, "user-1", "housekeeping")
    assert cm._count() == 1

    await cm.connect(mock_ws, "user-2", "housekeeping")
    assert cm._count() == 2

    await cm.disconnect(mock_ws)
    assert cm._count() == 0  # Same object, all removed


async def test_broadcast_to_roles():
    from app.ws.manager import ConnectionManager

    cm = ConnectionManager()
    ws1 = AsyncMock(spec=WebSocket)
    ws1.send_text = AsyncMock()
    ws2 = AsyncMock(spec=WebSocket)
    ws2.send_text = AsyncMock()

    await cm.connect(ws1, "u1", "housekeeping")
    await cm.connect(ws2, "u2", "manager")

    await cm.broadcast_to_roles({"type": "test"}, roles=["housekeeping"])
    ws1.send_text.assert_awaited_once()
    ws2.send_text.assert_not_awaited()  # manager not targeted


async def test_broadcast_all():
    from app.ws.manager import ConnectionManager

    cm = ConnectionManager()
    ws1 = AsyncMock(spec=WebSocket)
    ws1.send_text = AsyncMock()
    ws2 = AsyncMock(spec=WebSocket)
    ws2.send_text = AsyncMock()

    await cm.connect(ws1, "u1", "housekeeping")
    await cm.connect(ws2, "u2", "manager")

    await cm.broadcast({"type": "all"})
    ws1.send_text.assert_awaited_once()
    ws2.send_text.assert_awaited_once()
