"""测试多会话并发管理"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import orjson
from core.engine.manager import EngineSessionManager
from core.engine.runtime import WASMRuntime
from core.storage.vision import VisionStore
from core.storage.story import StoryStore


@pytest.fixture
def mock_runtime():
    """模拟运行时（同 test_session.py）"""
    runtime = MagicMock(spec=WASMRuntime)
    mock_handle = MagicMock()
    runtime.create_engine.return_value = mock_handle
    runtime.process.return_value = [orjson.dumps({"type": "engine_ready"}).decode("utf-8")]
    return runtime


@pytest.fixture
async def mock_stores():
    """模拟存储层"""
    vision_store = AsyncMock(spec=VisionStore)
    vision_store.load.return_value = None
    story_store = AsyncMock(spec=StoryStore)
    story_store.load_history.return_value = []
    return vision_store, story_store


@pytest.fixture
async def manager(mock_runtime, mock_stores):
    """创建管理器实例"""
    vision_store, story_store = mock_stores
    return EngineSessionManager(
        runtime=mock_runtime, vision_store=vision_store, story_store=story_store
    )


class TestEngineSessionManager:
    @pytest.mark.asyncio
    async def test_create_multiple_sessions(self, manager):
        """V6: 验证能创建多个会话"""
        session1 = await manager.get_or_create("session_1", "char_1", {}, {})
        session2 = await manager.get_or_create("session_2", "char_2", {}, {})

        assert session1.session_id == "session_1"
        assert session2.session_id == "session_2"
        assert session1 is not session2

        # 验证管理器中存储了两个会话
        assert len(manager._sessions) == 2

    @pytest.mark.asyncio
    async def test_get_existing_session(self, manager):
        """V6: 验证获取已有会话不重复创建"""
        session1 = await manager.get_or_create("session_1", "char_1", {}, {})
        session2 = await manager.get_or_create("session_1", "char_1", {}, {})

        assert session1 is session2  # 同一个实例
        assert len(manager._sessions) == 1

    @pytest.mark.asyncio
    async def test_concurrent_world_diff(self, manager):
        """V6: 验证并发 world_diff 不冲突"""
        # 创建两个会话
        session1 = await manager.get_or_create("session_1", "char_1", {}, {})
        session2 = await manager.get_or_create("session_2", "char_2", {}, {})

        # 模拟 world_diff 返回
        manager.runtime.process.return_value = [  # 修正：不是 _runtime
            orjson.dumps({"type": "mod_action", "session_id": None}).decode("utf-8")
        ]

        # 并发发送 world_diff
        async def send_diff(session, tick):
            return await session.on_world_diff(
                manager.runtime,  # 修正：不是 _runtime
                manager.vision_store,  # 修正：不是 _vision_store
                manager.story_store,  # 修正：不是 _story_store
                {"vision": {}, "tick": tick},  # 正确格式
            )

        results = await asyncio.gather(send_diff(session1, 100), send_diff(session2, 200))

        # 验证两个会话都正常返回
        assert len(results) == 2
        assert all(isinstance(r, list) for r in results)

    @pytest.mark.asyncio
    async def test_close_all_sessions(self, manager):
        """验证批量关闭会话"""
        await manager.get_or_create("session_1", "char_1", {}, {})
        await manager.get_or_create("session_2", "char_2", {}, {})

        await manager.close_all()

        # 验证所有会话已关闭
        assert len(manager._sessions) == 0

    @pytest.mark.asyncio
    async def test_session_isolation(self, manager):
        """V6: 验证会话状态隔离"""
        session1 = await manager.get_or_create("session_1", "char_1", {}, {})
        session2 = await manager.get_or_create("session_2", "char_2", {}, {})

        # 修改 session1 的状态
        session1.initialized = False

        # 验证 session2 不受影响
        assert session2.initialized is True
