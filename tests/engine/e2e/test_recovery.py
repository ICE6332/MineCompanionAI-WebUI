"""测试重启恢复机制"""

import pytest
import tempfile
from pathlib import Path
import orjson
from core.engine.runtime import WASMRuntime
from core.engine.manager import EngineSessionManager
from core.engine.session import EngineSession
from core.storage.vision import VisionStore
from core.storage.story import StoryStore


@pytest.fixture
async def temp_db():
    """创建临时数据库"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_recovery.db"
        yield str(db_path)


class TestRecovery:
    @pytest.mark.asyncio
    async def test_recover_after_restart(self, temp_db):
        """V4: 验证重启后能恢复 Vision 和 Story"""
        session_id = "recover_session"

        # === Phase 1: 初始化并写入数据 ===
        vision_store_1 = VisionStore(db_path=temp_db)
        story_store_1 = StoryStore(db_path=temp_db)
        await vision_store_1.init_schema()
        await story_store_1.init_schema()

        # 保存快照和历史
        vision_snapshot = {"entities": {"player": {"x": 100}}}
        await vision_store_1.save(session_id, vision_snapshot, 1000)

        story_node = {
            "id": "evt_1",
            "timestamp": 1000,
            "kind": "observation",
            "summary": "初始事件",
        }
        await story_store_1.append(session_id, story_node)

        # === Phase 2: 模拟重启（重新创建实例） ===
        vision_store_2 = VisionStore(db_path=temp_db)
        story_store_2 = StoryStore(db_path=temp_db)
        # 注意：不调用 init_schema，因为表已存在

        # 加载数据
        loaded_vision = await vision_store_2.load(session_id)
        loaded_story = await story_store_2.load_history(session_id)

        # V4: 验证数据恢复
        assert loaded_vision == vision_snapshot
        assert len(loaded_story) == 1
        assert loaded_story[0]["id"] == "evt_1"

    @pytest.mark.asyncio
    async def test_session_recovery_with_engine(self, temp_db):
        """V4: 验证会话重启后 Engine 能继续运行"""
        session_id = "engine_recover_session"

        # === Phase 1: 初始化会话 ===
        vision_store_1 = VisionStore(db_path=temp_db)
        story_store_1 = StoryStore(db_path=temp_db)
        await vision_store_1.init_schema()
        await story_store_1.init_schema()

        runtime_1 = WASMRuntime()
        manager_1 = EngineSessionManager(
            runtime=runtime_1, vision_store=vision_store_1, story_store=story_store_1
        )

        session_1 = await manager_1.get_or_create(
            session_id, "char_1", {"id": "char_1"}, {}
        )

        # 发送 world_diff 生成数据
        await session_1.on_world_diff(
            runtime_1, vision_store_1, story_store_1, {"vision": {}, "tick": 1000}  # 正确格式
        )

        # 关闭第一个 manager
        await manager_1.close_all()

        # === Phase 2: 模拟重启，重新创建 manager ===
        vision_store_2 = VisionStore(db_path=temp_db)
        story_store_2 = StoryStore(db_path=temp_db)

        runtime_2 = WASMRuntime()
        manager_2 = EngineSessionManager(
            runtime=runtime_2, vision_store=vision_store_2, story_store=story_store_2
        )

        # 重新初始化会话（应该加载历史数据）
        session_2 = await manager_2.get_or_create(
            session_id, "char_1", {"id": "char_1"}, {}
        )

        # V4: 验证新会话能继续运行
        outputs = await session_2.on_world_diff(
            runtime_2, vision_store_2, story_store_2, {"vision": {}, "tick": 2000}  # 正确格式
        )

        assert session_2.initialized is True
        assert isinstance(outputs, list)

        # 验证历史数据已加载
        loaded_story = await story_store_2.load_history(session_id)
        # 应该至少有 1 条历史记录（来自第一次 world_diff）
        assert len(loaded_story) >= 1
