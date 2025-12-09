"""
Unit tests for core/monitor/token_usage.py (Token Usage Tracker)

Tests the token usage tracking including:
- Hourly token aggregation
- 24-hour rolling window
- Trend data generation
- Expired data cleanup
- UTC timezone handling
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from core.monitor.token_usage import TokenUsageTracker


class TestTokenUsageTracker:
    """Tests for TokenUsageTracker class"""

    def test_initialization_with_empty_trend(self):
        """Should initialize with empty trend data"""
        tracker = TokenUsageTracker()

        trend = tracker.get_trend()

        assert trend.total_tokens == 0
        assert len(trend.trend) == 24  # 24 hours
        assert all(point.tokens == 0 for point in trend.trend)

    def test_record_aggregates_by_hour(self):
        """Should aggregate tokens by hour key"""
        tracker = TokenUsageTracker()

        fixed_time = datetime(2025, 12, 5, 10, 30, 0, tzinfo=timezone.utc)

        with patch("core.monitor.token_usage.datetime") as mock_datetime:
            # Configure mock to preserve real datetime class methods
            mock_datetime.now.return_value = fixed_time
            mock_datetime.strptime = datetime.strptime  # Use real strptime
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            # Record tokens in same hour
            tracker.record(100)
            tracker.record(50)
            tracker.record(25)

        # Check internal trend data (accessing private attribute for testing)
        hour_key = "2025-12-05 10:00"
        assert tracker._trend[hour_key] == 175

    def test_record_different_hours_separate_buckets(self):
        """Should store tokens in separate buckets for different hours"""
        tracker = TokenUsageTracker()

        # Record tokens at 10:00
        with patch("core.monitor.token_usage.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(
                2025, 12, 5, 10, 0, 0, tzinfo=timezone.utc
            )
            mock_datetime.strptime = datetime.strptime
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            tracker.record(100)

        # Record tokens at 11:00
        with patch("core.monitor.token_usage.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(
                2025, 12, 5, 11, 0, 0, tzinfo=timezone.utc
            )
            mock_datetime.strptime = datetime.strptime
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            tracker.record(200)

        # Verify separate buckets
        assert tracker._trend["2025-12-05 10:00"] == 100
        assert tracker._trend["2025-12-05 11:00"] == 200

    def test_record_cleans_up_expired_data(self):
        """Should remove data older than 24 hours"""
        tracker = TokenUsageTracker()

        base_time = datetime(2025, 12, 5, 12, 0, 0, tzinfo=timezone.utc)

        # Record token at 12:00
        with patch("core.monitor.token_usage.datetime") as mock_datetime:
            mock_datetime.now.return_value = base_time
            mock_datetime.strptime = datetime.strptime
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            tracker.record(100)

        # Record token 25 hours later (13:00 next day)
        with patch("core.monitor.token_usage.datetime") as mock_datetime:
            future_time = base_time + timedelta(hours=25)
            mock_datetime.now.return_value = future_time
            mock_datetime.strptime = datetime.strptime
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            tracker.record(200)

        # Old data (12:00) should be removed
        assert "2025-12-05 12:00" not in tracker._trend
        assert "2025-12-06 13:00" in tracker._trend

    def test_get_trend_returns_24_hours(self):
        """Should return trend with exactly 24 hourly points"""
        tracker = TokenUsageTracker()

        fixed_time = datetime(2025, 12, 5, 15, 0, 0, tzinfo=timezone.utc)

        with patch("core.monitor.token_usage.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.strptime = datetime.strptime
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            tracker.record(500)

            trend = tracker.get_trend()

        assert len(trend.trend) == 24

        # First point should be 23 hours ago
        first_point = trend.trend[0]
        expected_first_hour = (fixed_time - timedelta(hours=23)).strftime("%H:00")
        assert first_point.hour == expected_first_hour

        # Last point should be current hour
        last_point = trend.trend[-1]
        expected_last_hour = fixed_time.strftime("%H:00")
        assert last_point.hour == expected_last_hour

    def test_get_trend_includes_current_hour_data(self):
        """Should include tokens recorded in current hour"""
        tracker = TokenUsageTracker()

        fixed_time = datetime(2025, 12, 5, 14, 30, 0, tzinfo=timezone.utc)

        with patch("core.monitor.token_usage.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.strptime = datetime.strptime
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            tracker.record(300)

            trend = tracker.get_trend()

        # Current hour (14:00) should have 300 tokens
        current_hour_point = next(p for p in trend.trend if p.hour == "14:00")
        assert current_hour_point.tokens == 300

    def test_get_trend_calculates_total_tokens(self):
        """Should calculate total tokens across all hours"""
        tracker = TokenUsageTracker()

        base_time = datetime(2025, 12, 5, 10, 0, 0, tzinfo=timezone.utc)

        with patch("core.monitor.token_usage.datetime") as mock_datetime:
            # Record tokens across multiple hours
            for hour_offset in [0, 1, 2]:
                mock_datetime.now.return_value = base_time + timedelta(hours=hour_offset)
                mock_datetime.strptime = datetime.strptime
                mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
                tracker.record(100)

            # Get trend at hour 2
            mock_datetime.now.return_value = base_time + timedelta(hours=2)
            trend = tracker.get_trend()

        assert trend.total_tokens == 300

    def test_get_trend_timestamp_format(self):
        """Should include ISO format timestamp with timezone for each point"""
        tracker = TokenUsageTracker()

        fixed_time = datetime(2025, 12, 5, 16, 0, 0, tzinfo=timezone.utc)

        with patch("core.monitor.token_usage.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            trend = tracker.get_trend()

        # Check timestamp format for current hour point
        current_point = next(p for p in trend.trend if p.hour == "16:00")
        assert isinstance(current_point.timestamp, datetime)
        assert current_point.timestamp.tzinfo == timezone.utc

    def test_get_trend_last_updated_timestamp(self):
        """Should set last_updated to current hour (floored)"""
        tracker = TokenUsageTracker()

        fixed_time = datetime(2025, 12, 5, 14, 45, 30, tzinfo=timezone.utc)

        with patch("core.monitor.token_usage.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            trend = tracker.get_trend()

        # Should be floored to 14:00:00
        expected_time = datetime(2025, 12, 5, 14, 0, 0, tzinfo=timezone.utc)
        assert trend.last_updated == expected_time

    def test_record_and_get_trend_boundary_scenario(self):
        """Should handle recording and retrieving at hour boundaries"""
        tracker = TokenUsageTracker()

        # Record at 09:59:59
        with patch("core.monitor.token_usage.datetime") as mock_datetime:
            time_before = datetime(2025, 12, 5, 9, 59, 59, tzinfo=timezone.utc)
            mock_datetime.now.return_value = time_before
            mock_datetime.strptime = datetime.strptime
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            tracker.record(100)

        # Record at 10:00:01
        with patch("core.monitor.token_usage.datetime") as mock_datetime:
            time_after = datetime(2025, 12, 5, 10, 0, 1, tzinfo=timezone.utc)
            mock_datetime.now.return_value = time_after
            mock_datetime.strptime = datetime.strptime
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            tracker.record(200)

        # Should be in different buckets
        assert tracker._trend["2025-12-05 09:00"] == 100
        assert tracker._trend["2025-12-05 10:00"] == 200

    def test_empty_tracker_returns_zero_trend(self):
        """Should return trend with all zeros when no tokens recorded"""
        tracker = TokenUsageTracker()

        trend = tracker.get_trend()

        assert trend.total_tokens == 0
        assert all(point.tokens == 0 for point in trend.trend)
        assert len(trend.trend) == 24
