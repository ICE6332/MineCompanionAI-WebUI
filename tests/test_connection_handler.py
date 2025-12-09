"""
Unit tests for api/handlers/connection.py (Connection Init Handler)

Tests the connection initialization handler including:
- Connection acknowledgment response
- WebSocket send_json call
- Metrics recording
- Event bus publishing
- Response format validation
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from api.handlers.connection import ConnectionInitHandler
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
    context.client_id = "test-client-123"
    context.event_bus = Mock()
    context.event_bus.publish = Mock()
    context.metrics = Mock()
    context.metrics.record_message_sent = Mock()
    context.llm_service = Mock()
    context.conversation_context = Mock()
    return context


class TestConnectionInitHandler:
    """Tests for ConnectionInitHandler class"""

    @pytest.mark.asyncio
    async def test_handle_sends_connection_ack(self, mock_websocket, mock_context):
        """Should send connection_ack response via WebSocket"""
        handler = ConnectionInitHandler()
        message = {"type": "connection_init", "id": "init-123"}

        await handler.handle(mock_websocket, message, mock_context)

        # Verify send_json was called once
        mock_websocket.send_json.assert_called_once()

        # Verify response structure
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "connection_ack"
        assert call_args["data"]["client_id"] == "test-client-123"
        assert "timestamp" in call_args

    @pytest.mark.asyncio
    async def test_handle_response_format_correct(self, mock_websocket, mock_context):
        """Should return response with correct structure"""
        handler = ConnectionInitHandler()
        message = {"type": "connection_init"}

        response_str = await handler.handle(mock_websocket, message, mock_context)

        # Parse response string
        response = json.loads(response_str)

        assert response["type"] == "connection_ack"
        assert isinstance(response["timestamp"], str)
        assert response["data"]["client_id"] == "test-client-123"

    @pytest.mark.asyncio
    async def test_handle_timestamp_in_iso_format(self, mock_websocket, mock_context):
        """Should include ISO 8601 timestamp with timezone"""
        handler = ConnectionInitHandler()
        message = {"type": "connection_init"}

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
        handler = ConnectionInitHandler()
        message = {"type": "connection_init"}

        await handler.handle(mock_websocket, message, mock_context)

        # Verify metrics.record_message_sent was called
        mock_context.metrics.record_message_sent.assert_called_once_with(
            "connection_ack"
        )

    @pytest.mark.asyncio
    async def test_handle_publishes_message_sent_event(
        self, mock_websocket, mock_context
    ):
        """Should publish MESSAGE_SENT event to event bus"""
        handler = ConnectionInitHandler()
        message = {"type": "connection_init"}

        await handler.handle(mock_websocket, message, mock_context)

        # Verify event_bus.publish was called
        mock_context.event_bus.publish.assert_called_once()

        # Verify event type and data
        call_args = mock_context.event_bus.publish.call_args
        event_type = call_args[0][0]
        event_data = call_args[0][1]

        assert event_type == MonitorEventType.MESSAGE_SENT
        assert event_data["client_id"] == "test-client-123"
        assert event_data["message_type"] == "connection_ack"
        assert "timestamp" in event_data

    @pytest.mark.asyncio
    async def test_handle_returns_json_string(self, mock_websocket, mock_context):
        """Should return JSON string representation of response"""
        handler = ConnectionInitHandler()
        message = {"type": "connection_init"}

        response_str = await handler.handle(mock_websocket, message, mock_context)

        # Should be valid JSON
        assert isinstance(response_str, str)
        response = json.loads(response_str)  # Should not raise
        assert response["type"] == "connection_ack"
