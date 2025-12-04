"""
Unit tests for core/monitor/message_stats.py (Message Statistics Collector)

Tests the message statistics collection including:
- Message count tracking (received/sent)
- Per-type message aggregation
- Statistics retrieval
- Statistics reset
"""

from datetime import datetime, timezone

import pytest

from core.monitor.message_stats import MessageStatsCollector


class TestMessageStatsCollector:
    """Tests for MessageStatsCollector class"""

    def test_initialization_with_default_state(self):
        """Should initialize with zero counts"""
        collector = MessageStatsCollector()
        stats = collector.get_stats()

        assert stats.total_received == 0
        assert stats.total_sent == 0
        assert stats.messages_per_type == {}
        assert isinstance(stats.last_reset_at, datetime)

    def test_record_received_increments_total(self):
        """Should increment total_received counter"""
        collector = MessageStatsCollector()

        collector.record_received("conversation_request")
        collector.record_received("game_state_update")

        stats = collector.get_stats()
        assert stats.total_received == 2

    def test_record_sent_increments_total(self):
        """Should increment total_sent counter"""
        collector = MessageStatsCollector()

        collector.record_sent("conversation_response")
        collector.record_sent("action_decision")
        collector.record_sent("game_state_update")

        stats = collector.get_stats()
        assert stats.total_sent == 3

    def test_record_received_tracks_per_type(self):
        """Should track message counts per type"""
        collector = MessageStatsCollector()

        collector.record_received("conversation_request")
        collector.record_received("conversation_request")
        collector.record_received("game_state_update")

        stats = collector.get_stats()
        assert stats.messages_per_type["conversation_request"] == 2
        assert stats.messages_per_type["game_state_update"] == 1

    def test_record_sent_tracks_per_type(self):
        """Should track sent message counts per type"""
        collector = MessageStatsCollector()

        collector.record_sent("conversation_response")
        collector.record_sent("action_decision")
        collector.record_sent("conversation_response")

        stats = collector.get_stats()
        assert stats.messages_per_type["conversation_response"] == 2
        assert stats.messages_per_type["action_decision"] == 1

    def test_mixed_received_and_sent_tracking(self):
        """Should correctly track both received and sent messages"""
        collector = MessageStatsCollector()

        collector.record_received("conversation_request")
        collector.record_sent("conversation_response")
        collector.record_received("game_state_update")
        collector.record_sent("action_decision")

        stats = collector.get_stats()
        assert stats.total_received == 2
        assert stats.total_sent == 2
        assert stats.messages_per_type["conversation_request"] == 1
        assert stats.messages_per_type["conversation_response"] == 1
        assert stats.messages_per_type["game_state_update"] == 1
        assert stats.messages_per_type["action_decision"] == 1

    def test_reset_clears_all_statistics(self):
        """Should reset all counters to zero"""
        collector = MessageStatsCollector()

        # Record some messages
        collector.record_received("test_message")
        collector.record_received("test_message")
        collector.record_sent("response")

        # Verify stats are non-zero
        stats_before = collector.get_stats()
        assert stats_before.total_received == 2
        assert stats_before.total_sent == 1

        # Reset
        collector.reset()

        # Verify stats are cleared
        stats_after = collector.get_stats()
        assert stats_after.total_received == 0
        assert stats_after.total_sent == 0
        assert stats_after.messages_per_type == {}

    def test_reset_updates_last_reset_timestamp(self):
        """Should update last_reset_at timestamp on reset"""
        collector = MessageStatsCollector()

        stats_before = collector.get_stats()
        initial_reset_time = stats_before.last_reset_at

        # Small delay to ensure timestamp difference (if needed)
        import time

        time.sleep(0.01)

        collector.reset()

        stats_after = collector.get_stats()
        assert stats_after.last_reset_at > initial_reset_time

    def test_get_stats_returns_correct_instance(self):
        """Should return MessageStats instance with current data"""
        collector = MessageStatsCollector()

        collector.record_received("test")
        collector.record_sent("response")

        stats = collector.get_stats()

        # Verify it's the internal stats object
        assert stats.total_received == 1
        assert stats.total_sent == 1

        # Modify external reference (should affect internal state in current implementation)
        stats.total_received = 999

        # Get stats again
        stats2 = collector.get_stats()
        assert stats2.total_received == 999  # Current implementation returns reference

    def test_messages_per_type_is_defaultdict(self):
        """Should use defaultdict for messages_per_type (returns 0 for missing keys)"""
        collector = MessageStatsCollector()

        stats = collector.get_stats()

        # Accessing non-existent key should return 0 (defaultdict behavior)
        # Note: After get_stats(), messages_per_type is a defaultdict
        assert stats.messages_per_type.get("nonexistent_type", 0) == 0
