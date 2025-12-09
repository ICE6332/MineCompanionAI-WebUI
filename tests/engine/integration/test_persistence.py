"""测试 SQLite 持久化集成"""

import pytest
import tempfile
from pathlib import Path
import orjson
from core.storage.vision import VisionStore
from core.storage.story import StoryStore


@pytest.fixture
async def temp_db():
    """创建临时数据库"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_world.db"
        yield str(db_path)


@pytest.fixture
async def vision_store(temp_db):
    """创建 VisionStore 实例"""
    store = VisionStore(db_path=temp_db)
    await store.init_schema()
    return store


@pytest.fixture
async def story_store(temp_db):
    """创建 StoryStore 实例"""
    store = StoryStore(db_path=temp_db)
    await store.init_schema()
    return store


class TestVisionPersistence:
    @pytest.mark.asyncio
    async def test_save_and_load_snapshot(self, vision_store):
        """V4: 验证快照保存与加载"""
        session_id = "test_session"
        snapshot = {"entities": {"player": {"x": 100, "y": 64, "z": 200}}}
        tick = 1000

        await vision_store.save(session_id, snapshot, tick)

        loaded = await vision_store.load(session_id)
        assert loaded == snapshot

    @pytest.mark.asyncio
    async def test_upsert_snapshot(self, vision_store):
        """V4: 验证 UPSERT 幂等性"""
        session_id = "test_session"
        snapshot_v1 = {"entities": {"player": {"x": 100}}}
        snapshot_v2 = {"entities": {"player": {"x": 200}}}

        await vision_store.save(session_id, snapshot_v1, 1000)
        await vision_store.save(session_id, snapshot_v2, 2000)

        loaded = await vision_store.load(session_id)
        # 应该是最新的 v2
        assert loaded["entities"]["player"]["x"] == 200

    @pytest.mark.asyncio
    async def test_load_nonexistent_session(self, vision_store):
        """V4: 验证加载不存在的会话返回 None"""
        loaded = await vision_store.load("nonexistent_session")
        assert loaded is None


class TestStoryPersistence:
    @pytest.mark.asyncio
    async def test_append_and_load_history(self, story_store):
        """V4: 验证节点追加与加载"""
        session_id = "test_session"
        node1 = {"id": "evt_1", "timestamp": 1000, "kind": "observation", "summary": "事件1"}
        node2 = {"id": "evt_2", "timestamp": 2000, "kind": "action", "summary": "事件2"}

        await story_store.append(session_id, node1)
        await story_store.append(session_id, node2)

        history = await story_store.load_history(session_id, limit=10)

        # V4: 验证按时间倒序排列
        assert len(history) == 2
        assert history[0]["id"] == "evt_2"  # 最新的在前
        assert history[1]["id"] == "evt_1"

    @pytest.mark.asyncio
    async def test_load_history_limit(self, story_store):
        """V4: 验证历史加载限制"""
        session_id = "test_session"

        # 插入 5 个节点
        for i in range(5):
            node = {
                "id": f"evt_{i}",
                "timestamp": 1000 + i * 100,
                "kind": "observation",
                "summary": f"事件{i}",
            }
            await story_store.append(session_id, node)

        history = await story_store.load_history(session_id, limit=3)
        assert len(history) == 3
        # 应该是最新的 3 个
        assert history[0]["id"] == "evt_4"
        assert history[2]["id"] == "evt_2"

    @pytest.mark.asyncio
    async def test_load_empty_history(self, story_store):
        """V4: 验证加载空历史返回空列表"""
        history = await story_store.load_history("nonexistent_session")
        assert history == []


class TestPersistenceIntegration:
    @pytest.mark.asyncio
    async def test_vision_story_same_db(self, temp_db):
        """V4: 验证 Vision 和 Story 共享同一数据库"""
        vision_store = VisionStore(db_path=temp_db)
        story_store = StoryStore(db_path=temp_db)

        await vision_store.init_schema()
        await story_store.init_schema()

        # 同时写入数据
        await vision_store.save("session_1", {"data": "vision"}, 100)
        await story_store.append(
            "session_1",
            {"id": "evt_1", "timestamp": 100, "kind": "observation", "summary": "测试"},
        )

        # 验证都能读取
        vision_data = await vision_store.load("session_1")
        story_data = await story_store.load_history("session_1")

        assert vision_data is not None
        assert len(story_data) > 0
