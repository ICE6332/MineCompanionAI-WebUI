"""
Pytest configuration and shared fixtures for all tests.

This file is automatically loaded by pytest and provides common fixtures
that can be used across all test files.
"""

import pytest
from tests.fixtures.time_mock import mock_time
from tests.fixtures.websocket_mock import mock_websocket
from tests.fixtures.llm_mock import mock_llm


@pytest.fixture
def fixed_time():
    """
    Fixture to fix time to 2025-12-05 10:00:00 UTC.

    Yields:
        Context manager that patches datetime.now()

    Example:
        >>> def test_with_fixed_time(fixed_time):
        ...     with fixed_time:
        ...         # datetime.now() will return 2025-12-05 10:00:00 UTC
        ...         pass
    """
    return mock_time("2025-12-05T10:00:00")


@pytest.fixture
def mock_ws():
    """
    Fixture to create a mock WebSocket connection.

    Returns:
        MockWebSocket instance

    Example:
        >>> async def test_websocket(mock_ws):
        ...     await mock_ws.send_json({"type": "test"})
        ...     assert len(mock_ws.messages) == 1
    """
    return mock_websocket()


@pytest.fixture
def mock_llm_service():
    """
    Fixture to create a mock LLM service with default response.

    Returns:
        AsyncMock configured to return OpenAI-compatible responses

    Example:
        >>> async def test_llm(mock_llm_service):
        ...     response = await mock_llm_service.chat_completion(messages=[...])
        ...     assert "choices" in response
    """
    return mock_llm()


# Async test configuration
@pytest.fixture(scope="session")
def event_loop_policy():
    """
    Configure asyncio event loop policy for tests.

    Returns:
        The default event loop policy
    """
    import asyncio

    return asyncio.get_event_loop_policy()
