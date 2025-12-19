"""测试会话生命周期管理"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import orjson
from core.engine.session import EngineSession
from core.engine.runtime import WASMRuntime, EngineHandle
from core.storage.vision import VisionStore
from core.storage.story import StoryStore


@pytest.fixture
async def mock_stores():
    """模拟存储层"""
    vision_store = AsyncMock(spec=VisionStore)
    vision_store.load.return_value = None  # 无历史快照
    story_store = AsyncMock(spec=StoryStore)
    story_store.load_history.return_value = []  # 无历史节点
    return vision_store, story_store


@pytest.fixture
def mock_runtime():
    """模拟 WASM 运行时"""
    runtime = MagicMock(spec=WASMRuntime)
    mock_handle = MagicMock(spec=EngineHandle)
    runtime.create_engine.return_value = mock_handle

    # 模拟 process() 返回 engine_ready
    def mock_process(handle, input_json):
        input_data = orjson.loads(input_json)
        if input_data.get("type") == "init":
            return [orjson.dumps({"type": "engine_ready"}).decode("utf-8")]
        elif input_data.get("type") == "event":
            # 协议修复后，world_diff 被包装为 event 类型
            return [
                orjson.dumps({"type": "mod_action", "action": "move"}).decode("utf-8"),
                orjson.dumps({"type": "story_event", "id": "s1", "timestamp": 1, "kind": "observation", "summary": "测试"}).decode("utf-8"),
            ]
        return []

    runtime.process.side_effect = mock_process
    return runtime


class TestEngineSession:
    @pytest.mark.asyncio
    async def test_initialize_new_session(self, mock_runtime, mock_stores):
        """V3: 验证新会话初始化流程"""
        vision_store, story_store = mock_stores
        session = EngineSession(session_id="test_session_1", character_id="char_1")

        character_card = {"id": "char_1", "name": "测试角色"}
        config = {"max_tokens": 2000}

        outputs = await session.initialize(
            mock_runtime, vision_store, story_store, character_card, config
        )

        # V2: 验证使用 orjson
        assert mock_runtime.create_engine.called
        call_args = mock_runtime.create_engine.call_args[0][0]
        # 应该是 orjson 编码的字符串
        parsed = orjson.loads(call_args)
        # 实际 API 使用空 dict 作为config，不包含character
        assert isinstance(parsed, dict)

        # V3: 验证返回 engine_ready
        assert session.initialized is True
        assert len(outputs) == 1
        assert outputs[0]["type"] == "engine_ready"

    @pytest.mark.asyncio
    async def test_initialize_with_history(self, mock_runtime, mock_stores):
        """V4: 验证从历史恢复初始化"""
        vision_store, story_store = mock_stores

        # 模拟历史数据
        vision_store.load.return_value = {"entities": {"player": {"x": 100}}}
        story_store.load_history.return_value = [
            {"id": "story_1", "kind": "observation", "summary": "历史事件"}
        ]

        session = EngineSession(session_id="test_session_2", character_id="char_2")
        await session.initialize(mock_runtime, vision_store, story_store, {}, {})

        # 验证加载了历史数据 - 检查 process() 调用而不是 create_engine
        # create_engine 只接收 config（空dict），历史数据在 process(init_payload) 中
        init_call = mock_runtime.process.call_args_list[0]
        init_payload_str = init_call[0][1]
        parsed = orjson.loads(init_payload_str)
        # 协议修复后，vision 被规范化，但保留原始 entities 数据
        assert parsed["vision"]["entities"] == {"player": {"x": 100}}
        assert len(parsed["story_history"]) == 1

    @pytest.mark.asyncio
    async def test_on_world_diff_flow(self, mock_runtime, mock_stores):
        """V3: 验证 WorldDiff 处理流程"""
        vision_store, story_store = mock_stores
        session = EngineSession(session_id="test_session_3", character_id="char_3")

        # 先初始化
        await session.initialize(mock_runtime, vision_store, story_store, {}, {})

        # 发送 world_diff（正确格式：{vision, tick}）
        diff = {"vision": {}, "tick": 200}
        outputs = await session.on_world_diff(mock_runtime, vision_store, story_store, diff)

        # V3: 验证流程 Init → Event → mod_action (story_event 被持久化，不返回)
        # on_world_diff 只返回 mod_action 和 utterance，story_event 被持久化
        assert len(outputs) == 1
        assert outputs[0]["type"] == "mod_action"

        # V4: 验证持久化调用
        vision_store.save.assert_called_once()
        story_store.append.assert_called_once()

    @pytest.mark.asyncio
    async def test_orjson_used_throughout(self, mock_runtime, mock_stores):
        """V2: 验证全流程使用 orjson"""
        vision_store, story_store = mock_stores
        session = EngineSession(session_id="test_session_4", character_id="char_4")

        await session.initialize(mock_runtime, vision_store, story_store, {}, {})

        # 检查所有 runtime.process 调用都使用了 orjson 编码的字符串
        for call in mock_runtime.process.call_args_list:
            input_json = call[0][1]
            # 应该能直接用 orjson 解析
            parsed = orjson.loads(input_json)
            assert isinstance(parsed, dict)

    @pytest.mark.asyncio
    async def test_close_session(self, mock_runtime, mock_stores):
        """验证会话关闭清理"""
        vision_store, story_store = mock_stores
        session = EngineSession(session_id="test_session_5", character_id="char_5")

        await session.initialize(mock_runtime, vision_store, story_store, {}, {})

        mock_handle = mock_runtime.create_engine.return_value
        session.close()  # 不是 async 方法

        # 验证 handle.close() 被调用
        mock_handle.close.assert_called_once()
