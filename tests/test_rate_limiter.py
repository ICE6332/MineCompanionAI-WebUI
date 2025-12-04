"""
Unit tests for api/rate_limiter.py (WebSocket Rate Limiter)

Tests the sliding window rate limiting algorithm including:
- Basic rate limit checking
- Time window sliding and reset
- Multi-client isolation
- Quota calculation
- Client record clearing
- Custom configuration
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from api.rate_limiter import WebSocketRateLimiter


class TestWebSocketRateLimiter:
    """Tests for WebSocketRateLimiter class"""

    def test_initialization_with_defaults(self):
        """Should initialize with default parameters"""
        limiter = WebSocketRateLimiter()

        assert limiter.max_messages == 100
        assert limiter.window == timedelta(seconds=60)
        assert len(limiter.message_times) == 0

    def test_initialization_with_custom_config(self):
        """Should initialize with custom parameters"""
        limiter = WebSocketRateLimiter(max_messages=10, window_seconds=30)

        assert limiter.max_messages == 10
        assert limiter.window == timedelta(seconds=30)

    def test_first_message_passes(self):
        """Should allow first message from new client"""
        limiter = WebSocketRateLimiter()
        client_id = "client-123"

        result = limiter.check_rate_limit(client_id)

        assert result is True
        assert len(limiter.message_times[client_id]) == 1

    def test_messages_under_limit_all_pass(self):
        """Should allow all messages under the limit"""
        limiter = WebSocketRateLimiter(max_messages=10)
        client_id = "client-123"

        # Send 10 messages (should all pass)
        for i in range(10):
            result = limiter.check_rate_limit(client_id)
            assert result is True, f"Message {i+1} should pass"

        assert len(limiter.message_times[client_id]) == 10

    def test_message_over_limit_rejected(self):
        """Should reject message when limit is exceeded"""
        limiter = WebSocketRateLimiter(max_messages=5)
        client_id = "client-123"

        # Send 5 messages (should all pass)
        for _ in range(5):
            assert limiter.check_rate_limit(client_id) is True

        # 6th message should be rejected
        result = limiter.check_rate_limit(client_id)
        assert result is False
        assert len(limiter.message_times[client_id]) == 5  # Should not record rejected message

    def test_time_window_sliding_resets_limit(self):
        """Should reset limit after time window expires"""
        limiter = WebSocketRateLimiter(max_messages=3, window_seconds=60)
        client_id = "client-123"

        # Mock initial time: 2025-12-05 10:00:00 UTC
        initial_time = datetime(2025, 12, 5, 10, 0, 0, tzinfo=timezone.utc)

        with patch("api.rate_limiter.datetime") as mock_datetime:
            # Send 3 messages at 10:00:00 (all pass)
            mock_datetime.now.return_value = initial_time
            for _ in range(3):
                assert limiter.check_rate_limit(client_id) is True

            # 4th message at 10:00:00 should be rejected
            result = limiter.check_rate_limit(client_id)
            assert result is False

            # Advance time by 61 seconds (beyond window)
            mock_datetime.now.return_value = initial_time + timedelta(seconds=61)

            # Old records should be cleaned, new message should pass
            result = limiter.check_rate_limit(client_id)
            assert result is True
            assert len(limiter.message_times[client_id]) == 1  # Only 1 message in new window

    def test_multiple_clients_isolated(self):
        """Should isolate rate limits per client"""
        limiter = WebSocketRateLimiter(max_messages=3)
        client_a = "client-a"
        client_b = "client-b"

        # Client A sends 3 messages (all pass)
        for _ in range(3):
            assert limiter.check_rate_limit(client_a) is True

        # Client B should still be able to send messages
        for _ in range(3):
            result = limiter.check_rate_limit(client_b)
            assert result is True, "Client B should not be affected by Client A's limit"

        # Client A should be rate limited
        assert limiter.check_rate_limit(client_a) is False

        # Client B should still pass (3 messages sent, limit not reached)
        assert len(limiter.message_times[client_a]) == 3
        assert len(limiter.message_times[client_b]) == 3

    def test_get_remaining_quota_correct(self):
        """Should calculate remaining quota correctly"""
        limiter = WebSocketRateLimiter(max_messages=10)
        client_id = "client-123"

        # Initial quota should be full
        assert limiter.get_remaining_quota(client_id) == 10

        # Send 3 messages
        for _ in range(3):
            limiter.check_rate_limit(client_id)

        # Remaining quota should be 7
        assert limiter.get_remaining_quota(client_id) == 7

        # Send 7 more messages (total 10)
        for _ in range(7):
            limiter.check_rate_limit(client_id)

        # Remaining quota should be 0
        assert limiter.get_remaining_quota(client_id) == 0

    def test_get_remaining_quota_cleans_expired_records(self):
        """Should clean expired records when calculating quota"""
        limiter = WebSocketRateLimiter(max_messages=5, window_seconds=60)
        client_id = "client-123"

        initial_time = datetime(2025, 12, 5, 10, 0, 0, tzinfo=timezone.utc)

        with patch("api.rate_limiter.datetime") as mock_datetime:
            # Send 5 messages at 10:00:00
            mock_datetime.now.return_value = initial_time
            for _ in range(5):
                limiter.check_rate_limit(client_id)

            # Quota should be 0
            assert limiter.get_remaining_quota(client_id) == 0

            # Advance time by 61 seconds
            mock_datetime.now.return_value = initial_time + timedelta(seconds=61)

            # Quota should be restored to 5
            assert limiter.get_remaining_quota(client_id) == 5

    def test_clear_removes_client_records(self):
        """Should clear all records for a client"""
        limiter = WebSocketRateLimiter(max_messages=3)
        client_id = "client-123"

        # Send 3 messages (reach limit)
        for _ in range(3):
            limiter.check_rate_limit(client_id)

        assert len(limiter.message_times[client_id]) == 3
        assert limiter.check_rate_limit(client_id) is False  # Limit reached

        # Clear client records
        limiter.clear(client_id)

        # Client should not exist in message_times
        assert client_id not in limiter.message_times

        # New message should pass
        result = limiter.check_rate_limit(client_id)
        assert result is True
        assert len(limiter.message_times[client_id]) == 1

    def test_clear_nonexistent_client_no_error(self):
        """Should handle clearing nonexistent client gracefully"""
        limiter = WebSocketRateLimiter()
        client_id = "nonexistent-client"

        # Should not raise error
        limiter.clear(client_id)

        assert client_id not in limiter.message_times
