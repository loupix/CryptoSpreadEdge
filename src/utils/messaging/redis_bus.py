import asyncio
import json
import os
from typing import Any, Awaitable, Callable, Dict, Optional

try:
    # redis-py >= 4.x intègre aioredis sous redis.asyncio
    from redis.asyncio import Redis
except Exception:  # pragma: no cover
    Redis = None  # type: ignore


class RedisEventBus:
    """Event bus minimal basé sur Redis Streams (XADD / XREADGROUP).

    - publish: XADD sur un stream
    - consume: XGROUP CREATE (id='$' si absent), XREADGROUP en boucle, ack via XACK
    """

    def __init__(self, redis_url_env: str = "REDIS_URL"):
        self._redis: Optional[Redis] = None
        self._redis_url_env = redis_url_env
        self._is_running = False

    async def connect(self):
        if Redis is None:
            raise RuntimeError("redis.asyncio non disponible. Vérifiez la dépendance 'redis'.")
        url = os.getenv(self._redis_url_env, "redis://localhost:6379")
        self._redis = Redis.from_url(url, encoding="utf-8", decode_responses=True)

    async def close(self):
        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    async def publish(self, stream_name: str, message: Dict[str, Any]) -> Optional[str]:
        if self._redis is None:
            return None
        # Stocker payload JSON pour flexibilité
        payload = {"payload": json.dumps(message, default=str)}
        return await self._redis.xadd(stream_name, payload, maxlen=10_000, approximate=True)

    async def _ensure_group(self, stream_name: str, group_name: str):
        assert self._redis is not None
        try:
            groups = await self._redis.xinfo_groups(stream_name)
            if any(g.get("name") == group_name for g in groups):
                return
        except Exception:
            # Le stream peut ne pas exister encore
            pass
        try:
            await self._redis.xgroup_create(stream_name, group_name, id="$", mkstream=True)
        except Exception:
            # Conflits bénins en concurrence
            pass

    async def consume(
        self,
        stream_name: str,
        group_name: str,
        consumer_name: str,
        handler: Callable[[Dict[str, Any]], Awaitable[None]],
        block_ms: int = 2000,
        batch_size: int = 32,
    ):
        if self._redis is None:
            return
        await self._ensure_group(stream_name, group_name)
        self._is_running = True

        while self._is_running:
            try:
                entries = await self._redis.xreadgroup(
                    group_name,
                    consumer_name,
                    streams={stream_name: ">"},
                    count=batch_size,
                    block=block_ms,
                )
                if not entries:
                    continue
                for _, messages in entries:
                    for message_id, fields in messages:
                        try:
                            raw = fields.get("payload")
                            payload = json.loads(raw) if isinstance(raw, str) else raw
                            await handler(payload)
                            await self._redis.xack(stream_name, group_name, message_id)
                        except Exception:
                            # Ne pas ack pour permettre re-lecture; on pourrait loguer
                            pass
            except asyncio.CancelledError:  # pragma: no cover
                break
            except Exception:
                await asyncio.sleep(1)

    def stop(self):
        self._is_running = False

