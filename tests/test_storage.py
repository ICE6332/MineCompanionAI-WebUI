"""测试内存存储实现。"""

import asyncio
import pytest

from core.storage.memory import MemoryCacheStorage, MemoryStateStorage


@pytest.mark.asyncio
async def test_memory_cache_set_get_exists_delete():
    cache = MemoryCacheStorage()
    await cache.set("k", "v", ttl=1)
    assert await cache.exists("k")
    assert await cache.get("k") == "v"
    await cache.delete("k")
    assert not await cache.exists("k")


@pytest.mark.asyncio
async def test_memory_cache_expire():
    cache = MemoryCacheStorage()
    await cache.set("expire", "v", ttl=1)
    await asyncio.sleep(1.1)
    assert await cache.get("expire") is None


@pytest.mark.asyncio
async def test_memory_state_storage():
    state = MemoryStateStorage()
    await state.set_state("s1", {"a": 1})
    assert await state.get_state("s1") == {"a": 1}
