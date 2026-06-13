"""In-process event bus — modular monolith için loose coupling katmanı.

Kullanım:

    from app.core.events import events, DomainEvent

    @dataclass
    class ReservationCreated(DomainEvent):
        reservation_id: UUID
        guest_id: UUID

    # Yayıncı (örn. reservations router)
    await events.publish(ReservationCreated(reservation_id=r.id, guest_id=g.id))

    # Abone (örn. channel_sync_service)
    @events.subscribe(ReservationCreated)
    async def push_to_otas(evt: ReservationCreated, *, db: AsyncSession):
        ...

Tasarım notları:
  - Senkron-async hibrit: handler async ise await edilir, sync ise direkt çağrılır.
  - Bir handler hata atarsa diğerleri çalışmaya devam eder (fault isolation).
  - DB session handler'a opsiyonel olarak `db` kwarg ile iletilir.
  - Kafka/NATS migrasyonunda aynı API korunur; sadece `publish`'in iç gövdesi
    `producer.send(topic, evt)` olur.
"""
from __future__ import annotations

import asyncio
import inspect
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, TypeVar
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    """Tüm domain event'lerin temel sınıfı. Alt sınıflar @dataclass olmalı."""
    event_id: UUID = field(default_factory=uuid4, init=False)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), init=False)

    @property
    def name(self) -> str:
        return type(self).__name__


E = TypeVar("E", bound=DomainEvent)
Handler = Callable[..., Awaitable[Any] | Any]


class EventBus:
    """Basit in-process pub/sub. Tip-temelli; aynı tipe N handler abone olabilir."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: type[E]) -> Callable[[Handler], Handler]:
        def decorator(fn: Handler) -> Handler:
            self._handlers[event_type].append(fn)
            return fn
        return decorator

    def register(self, event_type: type[E], handler: Handler) -> None:
        """Decorator dışı kayıt (örn. test ortamında dinamik)."""
        self._handlers[event_type].append(handler)

    def unregister_all(self) -> None:
        self._handlers.clear()

    async def publish(self, event: DomainEvent, **context: Any) -> list[Any]:
        """Event'i tüm abonelere ilet. Hatalar izole edilir, geri kalanı çalışır."""
        results: list[Any] = []
        handlers = list(self._handlers.get(type(event), []))
        logger.debug("[EventBus] %s → %d handler", event.name, len(handlers))
        for h in handlers:
            try:
                # Handler'ın imzasında `db` veya başka context anahtarı varsa geçir
                sig = inspect.signature(h)
                kwargs = {k: v for k, v in context.items() if k in sig.parameters}
                ret = h(event, **kwargs)
                if inspect.isawaitable(ret):
                    ret = await ret
                results.append(ret)
            except Exception as exc:  # noqa: BLE001
                logger.exception("[EventBus] handler %s patladı: %s", getattr(h, "__name__", h), exc)
                results.append({"error": str(exc), "handler": getattr(h, "__name__", str(h))})
        return results


# Tek global örnek — modular monolith'in iletişim omurgası
events = EventBus()


# ── Domain event tanımları (bounded context'lere göre) ──

@dataclass
class ReservationCreated(DomainEvent):
    reservation_id: UUID = None  # type: ignore[assignment]
    guest_id: UUID | None = None
    room_type_id: UUID | None = None
    check_in: str | None = None
    check_out: str | None = None
    source: str | None = None


@dataclass
class ReservationCancelled(DomainEvent):
    reservation_id: UUID = None  # type: ignore[assignment]
    reason: str | None = None


@dataclass
class CheckInCompleted(DomainEvent):
    reservation_id: UUID = None  # type: ignore[assignment]
    guest_id: UUID | None = None
    room_id: UUID | None = None


@dataclass
class CheckOutCompleted(DomainEvent):
    reservation_id: UUID = None  # type: ignore[assignment]
    folio_total: float | None = None


@dataclass
class PaymentSucceeded(DomainEvent):
    txn_id: UUID = None  # type: ignore[assignment]
    folio_id: UUID | None = None
    amount: float | None = None


@dataclass
class RoomStatusChanged(DomainEvent):
    room_id: UUID = None  # type: ignore[assignment]
    old_status: str | None = None
    new_status: str | None = None
