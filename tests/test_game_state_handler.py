"""
Unit tests for api/handlers/game_state.py (Game State Handler)

Tests the game state update handler including:
- Game state acknowledgment response
- Player name extraction
- WebSocket send_json call
- Metrics recording
- Event bus publishing
- Response format validation
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from api.handlers.game_state import GameStateHandler
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
    """Create mock HandlerContext"""
    context = Mock(spec=HandlerContext)
    context.client_id = "test-client-456"
    context.event_bus = Mock()
    context.event_bus.publish = Mock()
    context.metrics = Mock()
    context.metrics.record_message_sent = Mock()
    context.llm_service = Mock()
    context.conversation_context = Mock()
    return context


class TestGameStateHandler:
    """Tests for GameStateHandler class"""

    @pytest.mark.asyncio
    async def test_handle_sends_game_state_ack(self, mock_websocket, mock_context):
        """Should send game_state_ack response via WebSocket"""
        handler = GameStateHandler()
        message = {
            "type": "game_state_update",
            "data": {"player_name": "Steve", "health": 20.0, "position": {"x": 100}},
        }

        await handler.handle(mock_websocket, message, mock_context)

        # Verify send_json was called once
        mock_websocket.send_json.assert_called_once()

        # Verify response structure
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "game_state_ack"
        assert call_args["data"]["status"] == "received"
        assert call_args["data"]["player"] == "Steve"

    @pytest.mark.asyncio
    async def test_handle_extracts_player_name_from_data(
        self, mock_websocket, mock_context
    ):
        """Should extract player name from game state data"""
        handler = GameStateHandler()
        message = {
            "type": "game_state_update",
            "data": {"player_name": "Alex", "world": "overworld"},
        }

        response_str = await handler.handle(mock_websocket, message, mock_context)
        response = json.loads(response_str)

        assert response["data"]["player"] == "Alex"

    @pytest.mark.asyncio
    async def test_handle_uses_unknown_for_missing_player_name(
        self, mock_websocket, mock_context
    ):
        """Should use 'Unknown' when player_name is missing"""
        handler = GameStateHandler()
        message = {"type": "game_state_update", "data": {"health": 18.0}}

        response_str = await handler.handle(mock_websocket, message, mock_context)
        response = json.loads(response_str)

        assert response["data"]["player"] == "Unknown"

    @pytest.mark.asyncio
    async def test_handle_with_empty_data(self, mock_websocket, mock_context):
        """Should handle message with empty data dict"""
        handler = GameStateHandler()
        message = {"type": "game_state_update", "data": {}}

        response_str = await handler.handle(mock_websocket, message, mock_context)
        response = json.loads(response_str)

        assert response["type"] == "game_state_ack"
        assert response["data"]["status"] == "received"
        assert response["data"]["player"] == "Unknown"

    @pytest.mark.asyncio
    async def test_handle_timestamp_in_iso_format(self, mock_websocket, mock_context):
        """Should include ISO 8601 timestamp with timezone"""
        handler = GameStateHandler()
        message = {"type": "game_state_update", "data": {"player_name": "Steve"}}

        response_str = await handler.handle(mock_websocket, message, mock_context)
        response = json.loads(response_str)

        timestamp = response["timestamp"]
        # Should be parseable as ISO format
        dt = datetime.fromisoformat(timestamp)
        # Should have timezone info
        assert dt.tzinfo is not None

    @pytest.mark.asyncio
    async def test_handle_records_message_sent_metric(
        self, mock_websocket, mock_context
    ):
        """Should record message_sent metric"""
        handler = GameStateHandler()
        message = {"type": "game_state_update", "data": {"player_name": "Steve"}}

        await handler.handle(mock_websocket, message, mock_context)

        # Verify metrics.record_message_sent was called
        mock_context.metrics.record_message_sent.assert_called_once_with(
            "game_state_ack"
        )

    @pytest.mark.asyncio
    async def test_handle_publishes_message_sent_event(
        self, mock_websocket, mock_context
    ):
        """Should publish MESSAGE_SENT event to event bus"""
        handler = GameStateHandler()
        message = {"type": "game_state_update", "data": {"player_name": "Alex"}}

        await handler.handle(mock_websocket, message, mock_context)

        # Verify event_bus.publish was called
        mock_context.event_bus.publish.assert_called_once()

        # Verify event type and data
        call_args = mock_context.event_bus.publish.call_args
        event_type = call_args[0][0]
        event_data = call_args[0][1]

        assert event_type == MonitorEventType.MESSAGE_SENT
        assert event_data["client_id"] == "test-client-456"
        assert event_data["message_type"] == "game_state_ack"
        assert "timestamp" in event_data
