"""
Time mocking utilities for tests.

Provides context managers and utilities for controlling time in tests.
"""

from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import patch
from typing import Generator


@contextmanager
def mock_time(iso_time: str) -> Generator[datetime, None, None]:
    """
    Context manager to fix datetime.now() to a specific ISO timestamp.

    Args:
        iso_time: ISO 8601 formatted time string (e.g., "2025-12-05T10:00:00")

    Yields:
        The fixed datetime object

    Example:
        >>> with mock_time("2025-12-05 10:00:00"):
        ...     print(datetime.now())  # Will always return 2025-12-05 10:00:00
    """
    # Parse ISO time string
    if "T" in iso_time:
        fixed_dt = datetime.fromisoformat(iso_time)
    else:
        # Support "YYYY-MM-DD HH:MM:SS" format
        fixed_dt = datetime.fromisoformat(iso_time.replace(" ", "T"))

    # Ensure UTC timezone
    if fixed_dt.tzinfo is None:
        fixed_dt = fixed_dt.replace(tzinfo=timezone.utc)

    with patch("datetime.datetime") as mock_datetime:
        # Mock now() to return fixed time
        mock_datetime.now.return_value = fixed_dt
        mock_datetime.utcnow.return_value = fixed_dt.replace(tzinfo=None)

        # Mock fromisoformat to work correctly
        mock_datetime.fromisoformat = datetime.fromisoformat

        # Mock timezone constants
        mock_datetime.timezone = datetime.timezone

        yield fixed_dt
