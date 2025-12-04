"""
WebSocket mocking utilities for tests.

Provides mock WebSocket implementations for testing WebSocket handlers.
"""

from typing import Any
from unittest.mock import AsyncMock


class MockWebSocket:
    """
    Mock WebSocket connection for testing.

    Simulates a WebSocket connection with send/receive capabilities.
    """

    def __init__(self):
        self.messages: list[str] = []
        self.is_closed = False
        self.client_state: dict[str, Any] = {}

    async def send_text(self, data: str) -> None:
        """
        Send text data (simulated).

        Args:
            data: Text message to send
        """
        if self.is_closed:
            raise RuntimeError("WebSocket is closed")
        self.messages.append(data)

    async def send_json(self, data: dict) -> None:
        """
        Send JSON data (simulated).

        Args:
            data: Dictionary to serialize and send
        """
        import json

        await self.send_text(json.dumps(data))

    async def receive_text(self) -> str:
        """
        Receive text data from queue.

        Returns:
            The next message in the queue

        Raises:
            RuntimeError: If no messages are available
        """
        if self.is_closed:
            raise RuntimeError("WebSocket is closed")
        if not self.messages:
            raise RuntimeError("No messages available")
        return self.messages.pop(0)

    async def receive_json(self) -> dict:
        """
        Receive JSON data from queue.

        Returns:
            Deserialized message dictionary
        """
        import json

        text = await self.receive_text()
        return json.loads(text)

    async def close(self) -> None:
        """Close the WebSocket connection."""
        self.is_closed = True

    async def accept(self) -> None:
        """Accept the WebSocket connection (no-op in mock)."""
        pass


def mock_websocket() -> MockWebSocket:
    """
    Factory function to create a mock WebSocket.

    Returns:
        A new MockWebSocket instance

    Example:
        >>> ws = mock_websocket()
        >>> await ws.send_json({"type": "test"})
        >>> assert ws.messages[0] == '{"type": "test"}'
    """
    return MockWebSocket()


def mock_websocket_with_messages(*messages: str) -> MockWebSocket:
    """
    Create a mock WebSocket pre-loaded with messages.

    Args:
        *messages: Messages to pre-load into the WebSocket queue

    Returns:
        MockWebSocket with messages ready to receive

    Example:
        >>> ws = mock_websocket_with_messages('{"type": "init"}', '{"type": "data"}')
        >>> msg = await ws.receive_text()
        >>> assert msg == '{"type": "init"}'
    """
    ws = MockWebSocket()
    ws.messages = list(messages)
    return ws
