"""存储接口定义，为未来 Redis 等后端准备。"""

from __future__ import annotations

from typing import Protocol, Optional, Any


class CacheStorage(Protocol):
    """缓存存储接口（LLM 响应缓存等场景）"""

    async def get(self, key: str) -> Optional[str]:
        ...

    async def set(self, key: str, value: str, ttl: int = 3600) -> None:
        ...

    async def exists(self, key: str) -> bool:
        ...

    async def delete(self, key: str) -> None:
        ...


class StateStorage(Protocol):
    """状态存储接口（会话/连接状态等）"""

    async def get_state(self, key: str) -> Optional[dict]:
        ...

    async def set_state(self, key: str, state: dict, ttl: Optional[int] = None) -> None:
        ...
