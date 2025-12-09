"""
Unit tests for core/monitor/connection_tracker.py (Connection Status Tracker)

Tests the connection status tracking including:
- Mod connection lifecycle
- Last message timestamp updates
- LLM status tracking
- Connection status retrieval
"""

from datetime import datetime, timezone

import pytest

from core.monitor.connection_tracker import ConnectionTracker


class TestConnectionTracker:
    """Tests for ConnectionTracker class"""

    def test_initialization_with_default_state(self):
        """Should initialize with disconnected state"""
        tracker = ConnectionTracker()
        status = tracker.get_status()

        assert status.mod_client_id is None
        assert status.mod_connected_at is None
        assert status.mod_last_message_at is None
        assert status.llm_provider is None
        assert status.llm_ready is False

    def test_set_mod_connected_records_client_id(self):
        """Should record mod client ID and connection timestamp"""
        tracker = ConnectionTracker()

        tracker.set_mod_connected("client-123")

        status = tracker.get_status()
        assert status.mod_client_id == "client-123"
        assert isinstance(status.mod_connected_at, datetime)
        assert status.mod_connected_at.tzinfo == timezone.utc

    def test_set_mod_disconnected_clears_connection(self):
        """Should clear mod connection information"""
        tracker = ConnectionTracker()

        # First connect
        tracker.set_mod_connected("client-123")
        status = tracker.get_status()
        assert status.mod_client_id == "client-123"

        # Then disconnect
        tracker.set_mod_disconnected()

        status = tracker.get_status()
        assert status.mod_client_id is None
        assert status.mod_connected_at is None

    def test_update_mod_last_message_sets_timestamp(self):
        """Should update last message timestamp"""
        tracker = ConnectionTracker()

        tracker.update_mod_last_message()

        status = tracker.get_status()
        assert isinstance(status.mod_last_message_at, datetime)
        assert status.mod_last_message_at.tzinfo == timezone.utc

    def test_update_mod_last_message_multiple_times(self):
        """Should update timestamp each time called"""
        tracker = ConnectionTracker()

        tracker.update_mod_last_message()
        status1 = tracker.get_status()
        first_timestamp = status1.mod_last_message_at

        import time

        time.sleep(0.01)  # Small delay to ensure timestamp difference

        tracker.update_mod_last_message()
        status2 = tracker.get_status()
        second_timestamp = status2.mod_last_message_at

        assert second_timestamp > first_timestamp

    def test_set_llm_status_records_provider_and_ready(self):
        """Should record LLM provider and ready status"""
        tracker = ConnectionTracker()

        tracker.set_llm_status("openai/gpt-4", True)

        status = tracker.get_status()
        assert status.llm_provider == "openai/gpt-4"
        assert status.llm_ready is True

    def test_set_llm_status_can_set_not_ready(self):
        """Should allow setting LLM status to not ready"""
        tracker = ConnectionTracker()

        # First set ready
        tracker.set_llm_status("anthropic/claude-3", True)

        # Then set not ready
        tracker.set_llm_status("anthropic/claude-3", False)

        status = tracker.get_status()
        assert status.llm_provider == "anthropic/claude-3"
        assert status.llm_ready is False

    def test_full_lifecycle_scenario(self):
        """Should handle complete connection lifecycle"""
        tracker = ConnectionTracker()

        # 1. Set LLM status
        tracker.set_llm_status("openai/gpt-4", True)

        # 2. Mod connects
        tracker.set_mod_connected("client-abc")

        # 3. Receive message
        tracker.update_mod_last_message()

        status = tracker.get_status()
        assert status.mod_client_id == "client-abc"
        assert status.mod_connected_at is not None
        assert status.mod_last_message_at is not None
        assert status.llm_provider == "openai/gpt-4"
        assert status.llm_ready is True

        # 4. Mod disconnects
        tracker.set_mod_disconnected()

        status = tracker.get_status()
        assert status.mod_client_id is None
        assert status.mod_connected_at is None
        # LLM status should remain
        assert status.llm_provider == "openai/gpt-4"
        assert status.llm_ready is True

    def test_get_status_returns_same_instance(self):
        """Should return reference to internal status object"""
        tracker = ConnectionTracker()

        tracker.set_mod_connected("client-123")

        status1 = tracker.get_status()
        status2 = tracker.get_status()

        # Should be the same object (current implementation)
        assert status1 is status2
        assert status1.mod_client_id == "client-123"
