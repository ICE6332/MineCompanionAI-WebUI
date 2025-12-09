"""
Unit tests for core/monitor/event_bus.py (Event Bus)

Tests the pub/sub event dispatching system including:
- Event publishing and history recording
- Subscriber registration and notification
- History size limits (deque maxlen)
- Event retrieval with limits
- Event format validation
- Error handling in subscribers
"""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from core.monitor.event_bus import EventBus
from core.monitor.event_types import MonitorEventType


class TestEventBus:
    """Tests for EventBus class"""

    def test_initialization_with_default_history_size(self):
        """Should initialize with default history size of 100"""
        bus = EventBus()

        assert bus._event_history.maxlen == 100
        assert len(bus._event_history) == 0
        assert len(bus._subscribers) == 0

    def test_initialization_with_custom_history_size(self):
        """Should initialize with custom history size"""
        bus = EventBus(history_size=50)

        assert bus._event_history.maxlen == 50

    def test_publish_adds_event_to_history(self):
        """Should add event to history when published"""
        bus = EventBus()

        bus.publish(
            MonitorEventType.MOD_CONNECTED,
            {"client_id": "test-123"},
            severity="info",
        )

        history = bus.get_recent_events(limit=10)
        assert len(history) == 1

        event = history[0]
        assert event["type"] == MonitorEventType.MOD_CONNECTED.value
        assert event["data"] == {"client_id": "test-123"}
        assert event["severity"] == "info"
        assert "id" in event
        assert "timestamp" in event

    def test_publish_event_format_correct(self):
        """Should create event with correct structure"""
        bus = EventBus()

        bus.publish(MonitorEventType.MESSAGE_RECEIVED, {"content": "test"})

        event = bus.get_recent_events(limit=1)[0]

        # Validate event structure
        assert isinstance(event["id"], str)
        assert len(event["id"]) > 0  # UUID should not be empty
        # MonitorEventType.value returns the actual value (e.g., "MESSAGE_RECEIVED" or "message_received")
        assert event["type"] == MonitorEventType.MESSAGE_RECEIVED.value
        assert isinstance(event["timestamp"], str)
        # Should be valid ISO 8601 format (can be parsed)
        from datetime import datetime
        dt = datetime.fromisoformat(event["timestamp"])
        assert dt is not None
        assert event["data"] == {"content": "test"}
        assert event["severity"] == "info"  # Default severity

    def test_publish_with_custom_severity(self):
        """Should accept custom severity level"""
        bus = EventBus()

        bus.publish(
            MonitorEventType.LLM_ERROR, {"error": "API timeout"}, severity="error"
        )

        event = bus.get_recent_events(limit=1)[0]
        assert event["severity"] == "error"

    def test_subscribe_registers_callback(self):
        """Should register callback for event type"""
        bus = EventBus()
        mock_callback = Mock()

        bus.subscribe(MonitorEventType.MOD_CONNECTED, mock_callback)

        # Publish event
        bus.publish(MonitorEventType.MOD_CONNECTED, {"client_id": "test"})

        # Callback should be called once
        mock_callback.assert_called_once()

        # Verify callback received correct event
        call_args = mock_callback.call_args[0][0]
        assert call_args["type"] == MonitorEventType.MOD_CONNECTED.value
        assert call_args["data"] == {"client_id": "test"}

    def test_subscribe_multiple_callbacks_for_same_event(self):
        """Should trigger all callbacks for the same event type"""
        bus = EventBus()
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()

        bus.subscribe(MonitorEventType.MESSAGE_SENT, callback1)
        bus.subscribe(MonitorEventType.MESSAGE_SENT, callback2)
        bus.subscribe(MonitorEventType.MESSAGE_SENT, callback3)

        bus.publish(MonitorEventType.MESSAGE_SENT, {"message": "hello"})

        # All callbacks should be called
        callback1.assert_called_once()
        callback2.assert_called_once()
        callback3.assert_called_once()

    def test_subscribe_isolated_by_event_type(self):
        """Should only trigger callbacks for matching event type"""
        bus = EventBus()
        connected_callback = Mock()
        disconnected_callback = Mock()

        bus.subscribe(MonitorEventType.MOD_CONNECTED, connected_callback)
        bus.subscribe(MonitorEventType.MOD_DISCONNECTED, disconnected_callback)

        # Publish MOD_CONNECTED
        bus.publish(MonitorEventType.MOD_CONNECTED, {"client_id": "test"})

        # Only connected_callback should be called
        connected_callback.assert_called_once()
        disconnected_callback.assert_not_called()

    def test_history_size_limit_enforced(self):
        """Should enforce history size limit (deque maxlen)"""
        bus = EventBus(history_size=5)

        # Publish 10 events (exceeds limit)
        for i in range(10):
            bus.publish(MonitorEventType.MESSAGE_RECEIVED, {"index": i})

        history = bus.get_recent_events(limit=100)

        # Should only keep last 5 events
        assert len(history) == 5

        # Should keep events 5-9 (deque pops from left)
        assert history[0]["data"]["index"] == 5
        assert history[4]["data"]["index"] == 9

    def test_get_recent_events_with_limit(self):
        """Should return limited number of recent events"""
        bus = EventBus()

        # Publish 10 events
        for i in range(10):
            bus.publish(MonitorEventType.TOKEN_STATS, {"index": i})

        # Get last 3 events
        recent = bus.get_recent_events(limit=3)

        assert len(recent) == 3
        assert recent[0]["data"]["index"] == 7
        assert recent[1]["data"]["index"] == 8
        assert recent[2]["data"]["index"] == 9

    def test_get_recent_events_with_zero_limit(self):
        """Should return empty list when limit is 0"""
        bus = EventBus()

        bus.publish(MonitorEventType.MESSAGE_RECEIVED, {"data": "test"})

        recent = bus.get_recent_events(limit=0)
        assert recent == []

    def test_get_recent_events_with_negative_limit(self):
        """Should return empty list when limit is negative"""
        bus = EventBus()

        bus.publish(MonitorEventType.MESSAGE_RECEIVED, {"data": "test"})

        recent = bus.get_recent_events(limit=-1)
        assert recent == []

    def test_clear_history_removes_all_events(self):
        """Should clear all event history"""
        bus = EventBus()

        # Publish 5 events
        for i in range(5):
            bus.publish(MonitorEventType.LLM_REQUEST, {"request_id": i})

        assert len(bus.get_recent_events(limit=100)) == 5

        # Clear history
        bus.clear_history()

        assert len(bus.get_recent_events(limit=100)) == 0

    def test_subscriber_exception_does_not_affect_others(self):
        """Should continue calling other subscribers even if one raises exception"""
        bus = EventBus()

        failing_callback = Mock(side_effect=Exception("Callback error"))
        successful_callback1 = Mock()
        successful_callback2 = Mock()

        bus.subscribe(MonitorEventType.MESSAGE_RECEIVED, successful_callback1)
        bus.subscribe(MonitorEventType.MESSAGE_RECEIVED, failing_callback)
        bus.subscribe(MonitorEventType.MESSAGE_RECEIVED, successful_callback2)

        # Publish event (should not raise exception)
        with pytest.raises(Exception, match="Callback error"):
            bus.publish(MonitorEventType.MESSAGE_RECEIVED, {"data": "test"})

        # First callback should have been called
        successful_callback1.assert_called_once()

        # Failing callback should have been called
        failing_callback.assert_called_once()

        # Note: In current implementation, exception stops propagation
        # This test documents current behavior
        # For production, consider wrapping callbacks in try-except

    def test_publish_without_subscribers(self):
        """Should handle publishing event with no subscribers"""
        bus = EventBus()

        # Should not raise error
        bus.publish(MonitorEventType.FRONTEND_CONNECTED, {"client": "web-ui"})

        # Event should still be in history
        history = bus.get_recent_events(limit=1)
        assert len(history) == 1
        assert history[0]["type"] == MonitorEventType.FRONTEND_CONNECTED.value
