"""测试 WebSocket 端到端流程"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import orjson
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from core.engine.runtime import WASMRuntime
from core.engine.manager import EngineSessionManager
from core.storage.vision import VisionStore
from core.storage.story import StoryStore
from api.handlers.engine_init import EngineInitHandler
from api.handlers.world_diff import WorldDiffHandler


@pytest.fixture
def mock_context():
    """模拟 WebSocket 处理上下文"""
    context = MagicMock()
    context.event_bus = MagicMock()
    context.event_bus.publish = MagicMock()  # 同步方法，不是 AsyncMock
    context.metrics = MagicMock()
    context.metrics.record_message_received = MagicMock()
    context.metrics.record_message_sent = MagicMock()
    return context


@pytest.fixture
async def mock_engine_manager():
    """模拟 Engine 管理器（返回实际响应）"""
    manager = AsyncMock(spec=EngineSessionManager)

    # 模拟 get_or_create 返回会话
    mock_session = MagicMock()
    mock_session.session_id = "test_session"
    mock_session.initialized = True

    # 模拟 on_world_diff 返回
    async def mock_world_diff(*args, **kwargs):
        return [
            {"type": "mod_action", "action": "move", "target": {"x": 100}},
            {"type": "utterance", "text": "测试回复"},
        ]

    mock_session.on_world_diff = mock_world_diff
    manager.get_or_create.return_value = mock_session

    return manager


@pytest.fixture
def mock_websocket():
    """模拟 WebSocket 连接"""
    ws = AsyncMock(spec=WebSocket)
    ws.send_text = AsyncMock()
    return ws


class TestEngineInitFlow:
    @pytest.mark.asyncio
    async def test_engine_init_handler(
        self, mock_websocket, mock_context, mock_engine_manager
    ):
        """V5: 验证 engine_init 消息处理"""
        handler = EngineInitHandler()
        message = {
            "type": "engine_init",
            "session_id": "test_session",
            "character_id": "char_1",
            "config": {},
        }

        # 注入 engine_manager
        mock_context.engine_manager = mock_engine_manager

        await handler.handle(mock_websocket, message, mock_context)

        # V5: 验证返回 engine_ready
        mock_websocket.send_text.assert_called_once()
        sent_data = mock_websocket.send_text.call_args[0][0]
        response = orjson.loads(sent_data)

        assert response["type"] == "engine_ready"
        assert response["session_id"] == "test_session"

        # V7: 验证监控事件发布
        mock_context.event_bus.publish.assert_called()


class TestWorldDiffFlow:
    @pytest.mark.asyncio
    async def test_world_diff_handler(
        self, mock_websocket, mock_context, mock_engine_manager
    ):
        """V5: 验证 world_diff 消息处理"""
        handler = WorldDiffHandler()
        message = {
            "type": "world_diff",
            "session_id": "test_session",
            "tick": 1000,
            "diff": {"entities": []},
        }

        mock_context.engine_manager = mock_engine_manager

        await handler.handle(mock_websocket, message, mock_context)

        # V5: 验证返回 mod_action 和 utterance
        assert mock_websocket.send_text.call_count == 2

        call_1 = orjson.loads(mock_websocket.send_text.call_args_list[0][0][0])
        call_2 = orjson.loads(mock_websocket.send_text.call_args_list[1][0][0])

        assert call_1["type"] == "mod_action"
        assert call_2["type"] == "utterance"

        # V7: 验证指标记录
        mock_context.metrics.record_message_received.assert_called_with("world_diff")
        mock_context.metrics.record_message_sent.assert_called()

    @pytest.mark.asyncio
    async def test_world_diff_no_session(
        self, mock_websocket, mock_context, mock_engine_manager
    ):
        """V5: 验证未初始化会话的错误处理"""
        handler = WorldDiffHandler()
        message = {
            "type": "world_diff",
            "session_id": "nonexistent_session",
            "tick": 1000,
            "diff": {},
        }

        # 模拟会话不存在
        mock_engine_manager.get_or_create.side_effect = Exception("会话未找到")
        mock_context.engine_manager = mock_engine_manager

        # 应该发送错误消息而不是崩溃
        await handler.handle(mock_websocket, message, mock_context)

        # 验证发送了错误响应
        sent_data = mock_websocket.send_text.call_args[0][0]
        response = orjson.loads(sent_data)
        assert response["type"] == "error"


class TestE2EFlow:
    @pytest.mark.asyncio
    async def test_full_flow_init_to_action(
        self, mock_websocket, mock_context, mock_engine_manager
    ):
        """V5: 验证完整流程 Init → WorldDiff → Action"""
        init_handler = EngineInitHandler()
        diff_handler = WorldDiffHandler()

        mock_context.engine_manager = mock_engine_manager

        # Step 1: engine_init
        init_msg = {
            "type": "engine_init",
            "session_id": "test_session",
            "character_id": "char_1",
            "config": {},
        }
        await init_handler.handle(mock_websocket, init_msg, mock_context)

        # 验证返回 engine_ready
        first_call = orjson.loads(mock_websocket.send_text.call_args_list[0][0][0])
        assert first_call["type"] == "engine_ready"

        # Step 2: world_diff
        diff_msg = {
            "type": "world_diff",
            "session_id": "test_session",
            "tick": 1000,
            "diff": {"entities": []},
        }
        await diff_handler.handle(mock_websocket, diff_msg, mock_context)

        # 验证返回 mod_action + utterance
        assert (
            mock_websocket.send_text.call_count >= 3
        )  # engine_ready + mod_action + utterance


class TestExistingFeatures:
    @pytest.mark.asyncio
    async def test_llm_dialogue_not_affected(self, mock_websocket, mock_context):
        """V7: 验证现有 LLM 对话功能不受影响"""
        # 导入现有的对话 handler
        from api.handlers.conversation import ConversationHandler

        handler = ConversationHandler()
        message = {
            "type": "conversation_request",
            "player_name": "Player",
            "message": "你好",
        }

        # 模拟 LLM 服务
        mock_context.llm_service = AsyncMock()
        mock_context.llm_service.chat_completion.return_value = {
            "choices": [{"message": {"content": "你好！"}}]
        }

        await handler.handle(mock_websocket, message, mock_context)

        # 验证 LLM 对话正常工作
        mock_context.llm_service.chat_completion.assert_called_once()
        mock_websocket.send_text.assert_called()
