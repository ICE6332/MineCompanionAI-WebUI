"""
LLM service mocking utilities for tests.

Provides mock LLM service implementations for testing without making real API calls.
"""

from typing import Any
from unittest.mock import AsyncMock


def mock_llm(response_content: str = "Mock response") -> AsyncMock:
    """
    Create a mock LLM service with fixed response.

    Args:
        response_content: The content to return in the mock response

    Returns:
        AsyncMock object configured to return an OpenAI-compatible response

    Example:
        >>> llm = mock_llm("Hello, world!")
        >>> response = await llm.chat_completion(messages=[...])
        >>> assert response["choices"][0]["message"]["content"] == "Hello, world!"
    """
    mock = AsyncMock()
    mock.chat_completion.return_value = {
        "id": "chatcmpl-mock",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": response_content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }
    return mock


def mock_llm_with_error(error_message: str = "API Error") -> AsyncMock:
    """
    Create a mock LLM service that raises an exception.

    Args:
        error_message: Error message to raise

    Returns:
        AsyncMock configured to raise an exception

    Example:
        >>> llm = mock_llm_with_error("Rate limit exceeded")
        >>> with pytest.raises(Exception, match="Rate limit exceeded"):
        ...     await llm.chat_completion(messages=[...])
    """
    mock = AsyncMock()
    mock.chat_completion.side_effect = Exception(error_message)
    return mock


def mock_llm_with_responses(*responses: str) -> AsyncMock:
    """
    Create a mock LLM service that returns different responses for each call.

    Args:
        *responses: Sequence of response contents to return

    Returns:
        AsyncMock that returns different responses on each call

    Example:
        >>> llm = mock_llm_with_responses("First", "Second", "Third")
        >>> r1 = await llm.chat_completion(messages=[...])
        >>> assert r1["choices"][0]["message"]["content"] == "First"
        >>> r2 = await llm.chat_completion(messages=[...])
        >>> assert r2["choices"][0]["message"]["content"] == "Second"
    """
    mock = AsyncMock()
    return_values = [
        {
            "id": f"chatcmpl-mock-{i}",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        }
        for i, content in enumerate(responses)
    ]
    mock.chat_completion.side_effect = return_values
    return mock
