"""
Unit tests for api/handlers/conversation.py (Conversation Handler)

Tests the conversation request handler including:
- LLM service integration
- Conversation context management
- CompactProtocol usage
- Token tracking
- Error handling
- Event publishing
- Response format
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from api.handlers.conversation import ConversationHandler
from api.handlers.context import HandlerContext
from core.monitor.event_types import MonitorEventType


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket"""
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


@pytest.fixture
def mock_context():
    """Create mock HandlerContext with LLM service"""
    context = Mock(spec=HandlerContext)
    context.client_id = "test-client-789"

    # Event bus
    context.event_bus = Mock()
    context.event_bus.publish = Mock()

    # Metrics
    context.metrics = Mock()
    context.metrics.record_message_sent = Mock()
    context.metrics.record_token_usage = Mock()

    # LLM service (AsyncMock for async call)
    context.llm_service = AsyncMock()
    context.llm_service.chat_completion = AsyncMock(
        return_value={
            "choices": [{"message": {"content": "Hello, I'm your AI companion!"}}],
            "usage": {"total_tokens": 50},
        }
    )

    # Conversation context
    context.conversation_context = Mock()
    context.conversation_context.get_history = Mock(return_value=[])
    context.conversation_context.add_message = Mock()

    return context


class TestConversationHandler:
    """Tests for ConversationHandler class"""

    @pytest.mark.asyncio
    async def test_handle_calls_llm_service(self, mock_websocket, mock_context):
        """Should call LLM service with correct messages"""
        handler = ConversationHandler()
        message = {
            "type": "conversation_request",
            "playerName": "Steve",
            "message": "Hello companion!",
            "id": "msg-123",
        }

        with patch("api.handlers.conversation.CompactProtocol") as mock_protocol:
            mock_protocol.parse.return_value = message
            mock_protocol.compact.return_value = {
                "t": "cr",
                "m": "Hello, I'm your AI companion!",
            }

            with patch("api.handlers.conversation.TokenTracker") as mock_tracker:
                mock_tracker.compare.return_value = {
                    "standard_tokens": 100,
                    "compact_tokens": 80,
                }

                await handler.handle(mock_websocket, message, mock_context)

        # Verify LLM service was called
        mock_context.llm_service.chat_completion.assert_called_once()

        # Verify messages structure
        call_args = mock_context.llm_service.chat_completion.call_args
        messages = call_args[1]["messages"]

        # Should have system prompt + user message
        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert "AICompanion" in messages[0]["content"]
        assert messages[-1]["role"] == "user"
        assert "Steve" in messages[-1]["content"]
        assert "Hello companion!" in messages[-1]["content"]

    @pytest.mark.asyncio
    async def test_handle_adds_messages_to_conversation_context(
        self, mock_websocket, mock_context
    ):
        """Should add both user and assistant messages to context"""
        handler = ConversationHandler()
        message = {
            "type": "conversation_request",
            "playerName": "Alex",
            "message": "How are you?",
            "id": "msg-456",
        }

        with patch("api.handlers.conversation.CompactProtocol") as mock_protocol:
            mock_protocol.parse.return_value = message
            mock_protocol.compact.return_value = {"t": "cr", "m": "I'm good!"}

            with patch("api.handlers.conversation.TokenTracker") as mock_tracker:
                mock_tracker.compare.return_value = {
                    "standard_tokens": 50,
                    "compact_tokens": 40,
                }

                await handler.handle(mock_websocket, message, mock_context)

        # Verify add_message was called twice (user + assistant)
        assert mock_context.conversation_context.add_message.call_count == 2

        # First call: user message
        first_call = mock_context.conversation_context.add_message.call_args_list[0]
        assert first_call[0][0] == "test-client-789"  # client_id
        assert first_call[1]["role"] == "user"
        assert "Alex" in first_call[1]["content"]

        # Second call: assistant message
        second_call = mock_context.conversation_context.add_message.call_args_list[1]
        assert second_call[1]["role"] == "assistant"
        assert isinstance(second_call[1]["content"], str)

    @pytest.mark.asyncio
    async def test_handle_sends_conversation_response(
        self, mock_websocket, mock_context
    ):
        """Should send conversation_response via WebSocket"""
        handler = ConversationHandler()
        message = {
            "type": "conversation_request",
            "playerName": "Steve",
            "message": "Test",
            "id": "msg-789",
            "companionName": "TestCompanion",
        }

        with patch("api.handlers.conversation.CompactProtocol") as mock_protocol:
            mock_protocol.parse.return_value = message
            mock_protocol.compact.return_value = {"t": "cr"}

            with patch("api.handlers.conversation.TokenTracker") as mock_tracker:
                mock_tracker.compare.return_value = {
                    "standard_tokens": 100,
                    "compact_tokens": 80,
                }

                await handler.handle(mock_websocket, message, mock_context)

        # Verify send_json was called
        mock_websocket.send_json.assert_called_once()

        # Verify response structure
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "conversation_response"
        assert call_args["id"] == "msg-789"
        assert call_args["companionName"] == "TestCompanion"
        assert isinstance(call_args["message"], str)

    @pytest.mark.asyncio
    async def test_handle_publishes_llm_request_event(
        self, mock_websocket, mock_context
    ):
        """Should publish LLM_REQUEST event before calling LLM"""
        handler = ConversationHandler()
        message = {
            "type": "conversation_request",
            "playerName": "Steve",
            "message": "Test message",
        }

        with patch("api.handlers.conversation.CompactProtocol") as mock_protocol:
            mock_protocol.parse.return_value = message
            mock_protocol.compact.return_value = {"t": "cr"}

            with patch("api.handlers.conversation.TokenTracker") as mock_tracker:
                mock_tracker.compare.return_value = {
                    "standard_tokens": 100,
                    "compact_tokens": 80,
                }

                await handler.handle(mock_websocket, message, mock_context)

        # Verify LLM_REQUEST event was published
        published_events = [
            call[0][0] for call in mock_context.event_bus.publish.call_args_list
        ]
        assert MonitorEventType.LLM_REQUEST in published_events

    @pytest.mark.asyncio
    async def test_handle_publishes_llm_response_event(
        self, mock_websocket, mock_context
    ):
        """Should publish LLM_RESPONSE event after successful LLM call"""
        handler = ConversationHandler()
        message = {"type": "conversation_request", "playerName": "Alex", "message": "Hi"}

        with patch("api.handlers.conversation.CompactProtocol") as mock_protocol:
            mock_protocol.parse.return_value = message
            mock_protocol.compact.return_value = {"t": "cr"}

            with patch("api.handlers.conversation.TokenTracker") as mock_tracker:
                mock_tracker.compare.return_value = {
                    "standard_tokens": 100,
                    "compact_tokens": 80,
                }

                await handler.handle(mock_websocket, message, mock_context)

        # Verify LLM_RESPONSE event was published
        published_events = [
            call[0][0] for call in mock_context.event_bus.publish.call_args_list
        ]
        assert MonitorEventType.LLM_RESPONSE in published_events

    @pytest.mark.asyncio
    async def test_handle_llm_error_publishes_error_event(
        self, mock_websocket, mock_context
    ):
        """Should publish LLM_ERROR event when LLM call fails"""
        # Configure LLM to raise exception
        mock_context.llm_service.chat_completion.side_effect = Exception("API timeout")

        handler = ConversationHandler()
        message = {"type": "conversation_request", "playerName": "Steve", "message": "Hi"}

        with patch("api.handlers.conversation.CompactProtocol") as mock_protocol:
            mock_protocol.parse.return_value = message
            mock_protocol.compact.return_value = {"t": "cr"}

            with patch("api.handlers.conversation.TokenTracker") as mock_tracker:
                mock_tracker.compare.return_value = {
                    "standard_tokens": 100,
                    "compact_tokens": 80,
                }

                await handler.handle(mock_websocket, message, mock_context)

        # Verify LLM_ERROR event was published
        published_events = [
            call[0][0] for call in mock_context.event_bus.publish.call_args_list
        ]
        assert MonitorEventType.LLM_ERROR in published_events

    @pytest.mark.asyncio
    async def test_handle_llm_error_returns_default_reply(
        self, mock_websocket, mock_context
    ):
        """Should return default reply when LLM fails"""
        # Configure LLM to raise exception
        mock_context.llm_service.chat_completion.side_effect = Exception("API error")

        handler = ConversationHandler()
        message = {
            "type": "conversation_request",
            "playerName": "Steve",
            "message": "Hi",
            "id": "msg-999",
        }

        with patch("api.handlers.conversation.CompactProtocol") as mock_protocol:
            mock_protocol.parse.return_value = message
            mock_protocol.compact.return_value = {"t": "cr"}

            with patch("api.handlers.conversation.TokenTracker") as mock_tracker:
                mock_tracker.compare.return_value = {
                    "standard_tokens": 100,
                    "compact_tokens": 80,
                }

                response_str = await handler.handle(
                    mock_websocket, message, mock_context
                )

        response = json.loads(response_str)
        # Should contain default error message
        assert "抱歉" in response["message"] or "无法响应" in response["message"]

    @pytest.mark.asyncio
    async def test_handle_records_token_usage(self, mock_websocket, mock_context):
        """Should record token usage metric"""
        handler = ConversationHandler()
        message = {"type": "conversation_request", "playerName": "Steve", "message": "Hi"}

        with patch("api.handlers.conversation.CompactProtocol") as mock_protocol:
            mock_protocol.parse.return_value = message
            mock_protocol.compact.return_value = {"t": "cr"}

            with patch("api.handlers.conversation.TokenTracker") as mock_tracker:
                mock_tracker.compare.return_value = {
                    "standard_tokens": 100,
                    "compact_tokens": 80,
                }

                await handler.handle(mock_websocket, message, mock_context)

        # Verify record_token_usage was called
        mock_context.metrics.record_token_usage.assert_called_once_with(80)

    @pytest.mark.asyncio
    async def test_handle_publishes_token_stats_event(
        self, mock_websocket, mock_context
    ):
        """Should publish TOKEN_STATS event"""
        handler = ConversationHandler()
        message = {"type": "conversation_request", "playerName": "Alex", "message": "Test"}

        with patch("api.handlers.conversation.CompactProtocol") as mock_protocol:
            mock_protocol.parse.return_value = message
            mock_protocol.compact.return_value = {"t": "cr"}

            with patch("api.handlers.conversation.TokenTracker") as mock_tracker:
                mock_tracker.compare.return_value = {
                    "standard_tokens": 150,
                    "compact_tokens": 120,
                }

                await handler.handle(mock_websocket, message, mock_context)

        # Verify TOKEN_STATS event was published
        published_events = [
            call[0][0] for call in mock_context.event_bus.publish.call_args_list
        ]
        assert MonitorEventType.TOKEN_STATS in published_events
