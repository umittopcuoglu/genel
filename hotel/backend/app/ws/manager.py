"""
WebSocket bağlantı yöneticisi.
- ConnectionManager: aktif bağlantıları yönetir
- Redis Pub/Sub ile çoklu worker desteği
"""
import asyncio
import json
import logging
from typing import Optional
from fastapi import WebSocket
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
    _redis_pool = None

    async def get_redis():
        global _redis_pool
        if _redis_pool is None:
            redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
            _redis_pool = aioredis.ConnectionPool.from_url(redis_url, decode_responses=True)
        return aioredis.Redis(connection_pool=_redis_pool)

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

    async def get_redis():
        return None


class ConnectionManager:
    """Aktif WebSocket bağlantılarını yönetir."""

    def __init__(self):
        self._connections: dict[str, list[dict]] = {}  # role -> [{websocket, user_id}]

    async def connect(self, ws: WebSocket, user_id: str, role: str):
        await ws.accept()
        if role not in self._connections:
            self._connections[role] = []
        self._connections[role].append({"ws": ws, "user_id": user_id})
        logger.info("WS bağlandı: user=%s role=%s (toplam %d)", user_id, role, self._count())

    async def disconnect(self, ws: WebSocket):
        # Aynı ws nesnesinin TÜM kayıtlarını (tüm rollerde) kaldır
        for role, conns in list(self._connections.items()):
            for c in list(conns):
                if c["ws"] is ws:
                    conns.remove(c)
                    logger.info("WS koptu: user=%s (kalan %d)", c["user_id"], self._count())
            if not conns:
                del self._connections[role]

    async def broadcast(self, event: dict):
        """Tüm bağlı istemcilere yayınla."""
        payload = json.dumps(event, default=str)
        for conns in self._connections.values():
            for c in conns:
                try:
                    await c["ws"].send_text(payload)
                except Exception:
                    pass

    async def broadcast_to_roles(self, event: dict, roles: list[str]):
        """Belirli rollere yayınla."""
        payload = json.dumps(event, default=str)
        for role in roles:
            for c in self._connections.get(role, []):
                try:
                    await c["ws"].send_text(payload)
                except Exception:
                    pass

    async def _redis_listener(self, channel: str = "hotelops:events"):
        """Redis Pub/Sub dinleyicisi — çoklu worker desteği."""
        if not REDIS_AVAILABLE:
            return
        try:
            r = await get_redis()
            if r is None:
                return
            pubsub = r.pubsub()
            await pubsub.subscribe(channel)
            logger.info("Redis Pub/Sub dinleyicisi başladı: %s", channel)
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        event = json.loads(message["data"])
                        await self.broadcast(event)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning("Redis Pub/Sub dinleyici hatası (Redis yoksa önemsiz): %s", e)

    async def publish_event(self, event: dict, channel: str = "hotelops:events"):
        """Event'i Redis Pub/Sub'da yayınla (worker'lar arası)."""
        if not REDIS_AVAILABLE:
            return
        try:
            r = await get_redis()
            if r is not None:
                await r.publish(channel, json.dumps(event, default=str))
        except Exception as e:
            logger.warning("Redis publish hatası: %s", e)

    def _count(self) -> int:
        return sum(len(c) for c in self._connections.values())


# Singleton
manager = ConnectionManager()
