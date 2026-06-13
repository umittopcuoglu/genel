"""Domain event abonelikleri — modular monolith'in cross-context entegrasyonu.

Bu modül `main.py` lifespan'inde import edilir; import işlemi handler'ları
EventBus'a kaydeder. Cross-context bağımlılıklar yalnızca buradan geçer; iş
mantığı modülleri (reservations, channel_sync, vb.) birbirini bilmek zorunda
kalmaz.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import (
    CheckInCompleted,
    CheckOutCompleted,
    PaymentSucceeded,
    ReservationCancelled,
    ReservationCreated,
    events,
)
from app.models.crm import CommunicationLog
from app.models.front_office import Guest

logger = logging.getLogger(__name__)


# ── ReservationCreated → CRM welcome log ──

@events.subscribe(ReservationCreated)
async def crm_welcome_on_reservation(event: ReservationCreated, db: AsyncSession | None = None):
    """Yeni rezervasyon → misafir için welcome iletişim kaydı (idempotent)."""
    if db is None or event.guest_id is None:
        return
    guest = await db.get(Guest, event.guest_id)
    if guest is None:
        return
    db.add(
        CommunicationLog(
            guest_id=guest.id,
            channel="email",
            direction="outbound",
            subject="Rezervasyonunuz alındı",
            body=(
                f"Sayın {guest.first_name} {guest.last_name}, "
                f"{event.check_in} – {event.check_out} tarihli rezervasyonunuz oluşturuldu."
            ),
            status="queued",
            external_ref=f"EVT-{event.event_id.hex[:8]}",
        )
    )
    # commit dışarıdan — çağıran transaction'a katılır


# ── ReservationCreated → audit/log ──

@events.subscribe(ReservationCreated)
async def log_reservation_created(event: ReservationCreated, db: AsyncSession | None = None):
    logger.info(
        "[event] ReservationCreated id=%s guest=%s source=%s",
        event.reservation_id, event.guest_id, event.source,
    )


# ── CheckIn / CheckOut / Cancel — bilgilendirme logları (genişletilebilir) ──

@events.subscribe(CheckInCompleted)
async def log_checkin(event: CheckInCompleted, db: AsyncSession | None = None):
    logger.info("[event] CheckInCompleted reservation=%s", event.reservation_id)


@events.subscribe(CheckOutCompleted)
async def log_checkout(event: CheckOutCompleted, db: AsyncSession | None = None):
    logger.info("[event] CheckOutCompleted reservation=%s total=%s", event.reservation_id, event.folio_total)


@events.subscribe(ReservationCancelled)
async def log_cancel(event: ReservationCancelled, db: AsyncSession | None = None):
    logger.info("[event] ReservationCancelled reservation=%s reason=%s", event.reservation_id, event.reason)


@events.subscribe(PaymentSucceeded)
async def log_payment(event: PaymentSucceeded, db: AsyncSession | None = None):
    logger.info("[event] PaymentSucceeded txn=%s amount=%s", event.txn_id, event.amount)


# ── B4: ReservationCreated → Channel Manager push ──

@events.subscribe(ReservationCreated)
async def channel_sync_on_reservation(event: ReservationCreated, db: AsyncSession | None = None):
    """Yeni rezervasyon → tüm aktif OTA kanallarına envanter güncelleme push'la."""
    if db is None or event.room_type_id is None:
        return
    from datetime import date
    from app.services.channel_sync_service import ChannelSyncService
    try:
        check_in = date.fromisoformat(event.check_in) if isinstance(event.check_in, str) else event.check_in
        check_out = date.fromisoformat(event.check_out) if isinstance(event.check_out, str) else event.check_out
        await ChannelSyncService.push_inventory_update(
            db, event.room_type_id, check_in, check_out, trigger="reservation", commit=True
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[event] channel_sync_on_reservation hata: %s", exc)


# ── B4: ReservationCancelled → Channel Manager push (envanter geri) ──

@events.subscribe(ReservationCancelled)
async def channel_sync_on_cancel(event: ReservationCancelled, db: AsyncSession | None = None):
    """Rezervasyon iptal → OTA kanallarına stok geri-açıldı push'la."""
    if db is None:
        return
    from app.services.channel_sync_service import ChannelSyncService
    from app.models.front_office import Reservation
    try:
        res = await db.get(Reservation, event.reservation_id)
        if res is None or res.room_type_id is None:
            return
        await ChannelSyncService.push_inventory_update(
            db, res.room_type_id, res.check_in, res.check_out, trigger="cancel", commit=True
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[event] channel_sync_on_cancel hata: %s", exc)


def register_all() -> int:
    """Çağrım sayısını kolay görmek için: kaç handler register edilmiş."""
    return sum(len(v) for v in events._handlers.values())
