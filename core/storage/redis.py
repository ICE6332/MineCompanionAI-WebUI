"""Redis 存储实现（可选，生产可开启）。"""

from __future__ import annotations

from typing import Optional

try:
    import redis.asyncio as aioredis
except ImportError as exc:  # pragma: no cover - 可选依赖
    aioredis = None

from core.storage.interfaces import CacheStorage


class RedisCacheStorage(CacheStorage):
    """Redis 缓存实现。"""

    def __init__(self, url: str = "redis://localhost:6379"):
        if aioredis is None:
            raise ImportError("redis dependency not installed; install with extra 'redis'.")
        self._redis = aioredis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, ttl: int = 3600) -> None:
        await self._redis.setex(key, ttl, value)

    async def exists(self, key: str) -> bool:
        return await self._redis.exists(key) > 0

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def close(self) -> None:
        await self._redis.close()
