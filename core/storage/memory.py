"""内存存储实现，开发/测试使用。"""

from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from core.storage.interfaces import CacheStorage, StateStorage


class MemoryCacheStorage(CacheStorage):
    """内存缓存实现。"""

    def __init__(self) -> None:
        self._cache: Dict[str, tuple[str, datetime]] = {}

    async def get(self, key: str) -> Optional[str]:
        if key not in self._cache:
            return None
        value, expires_at = self._cache[key]
        if datetime.now(timezone.utc) > expires_at:
            del self._cache[key]
            return None
        return value

    async def set(self, key: str, value: str, ttl: int = 3600) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        self._cache[key] = (value, expires_at)

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def delete(self, key: str) -> None:
        self._cache.pop(key, None)


class MemoryStateStorage(StateStorage):
    """简单状态存储（无过期）。"""

    def __init__(self) -> None:
        self._state: Dict[str, Any] = {}

    async def get_state(self, key: str) -> Optional[dict]:
        return self._state.get(key)

    async def set_state(self, key: str, state: dict, ttl: Optional[int] = None) -> None:
        # 当前版本忽略 ttl
        self._state[key] = state
