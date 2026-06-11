"""
WebSocket olay yayıncıları.
Her olay fonksiyonu event'i hazırlar ve `manager.publish_event()` ile yayınlar.
"""
from datetime import datetime, timezone
from app.ws.manager import manager


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


async def emit_room_status_changed(room_id: str, room_no: str,
                                    old_status: str, new_status: str):
    """Oda durumu değişti — tüm rollere."""
    event = {
        "type": "room.status.changed",
        "data": {
            "room_id": str(room_id),
            "room_no": room_no,
            "old_status": old_status,
            "new_status": new_status,
        },
        "ts": _ts(),
    }
    await manager.publish_event(event)
    await manager.broadcast(event)


async def emit_reservation_created(reservation_data: dict):
    """Rezervasyon oluşturuldu — tüm rollere."""
    event = {
        "type": "reservation.created",
        "data": reservation_data,
        "ts": _ts(),
    }
    await manager.publish_event(event)
    await manager.broadcast(event)


async def emit_checkin(reservation_id: str, room_no: str, guest_name: str):
    """Check-in yapıldı — tüm rollere."""
    event = {
        "type": "checkin",
        "data": {
            "reservation_id": str(reservation_id),
            "room_no": room_no,
            "guest_name": guest_name,
        },
        "ts": _ts(),
    }
    await manager.publish_event(event)
    await manager.broadcast(event)


async def emit_checkout(reservation_id: str, room_no: str, guest_name: str):
    """Check-out yapıldı — tüm rollere."""
    event = {
        "type": "checkout",
        "data": {
            "reservation_id": str(reservation_id),
            "room_no": room_no,
            "guest_name": guest_name,
        },
        "ts": _ts(),
    }
    await manager.publish_event(event)
    await manager.broadcast(event)


async def emit_housekeeping_task(task_data: dict):
    """Housekeeping görevi oluşturuldu/güncellendi — sadece housekeeping rolleri."""
    event = {
        "type": "housekeeping.task",
        "data": task_data,
        "ts": _ts(),
    }
    await manager.publish_event(event)
    await manager.broadcast_to_roles(event, ["housekeeping", "manager", "superadmin", "frontdesk"])
