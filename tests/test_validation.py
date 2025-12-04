"""
Unit tests for api/validation.py (Pydantic Models)

Tests the WebSocket message validation models including:
- ConnectionInitMessage validation
- GameStateUpdateMessage validation
- ConversationRequestMessage validation
- ModMessage validation
- MonitorCommand validation
- Field constraints (min_length, max_length)
- Custom validators
"""

import pytest
from pydantic import ValidationError

from api.validation import (
    ConnectionInitMessage,
    ConversationRequestMessage,
    GameStateUpdateMessage,
    ModMessage,
    MonitorCommand,
)


class TestConnectionInitMessage:
    """Tests for ConnectionInitMessage model"""

    def test_valid_connection_init_message(self):
        """Should accept valid connection_init message"""
        msg = ConnectionInitMessage(
            type="connection_init",
            id="test-id-123",
            data={"client_version": "1.0.0"},
        )

        assert msg.type == "connection_init"
        assert msg.id == "test-id-123"
        assert msg.data == {"client_version": "1.0.0"}

    def test_connection_init_with_minimal_fields(self):
        """Should accept message with only required fields"""
        msg = ConnectionInitMessage(type="connection_init")

        assert msg.type == "connection_init"
        assert msg.id is None
        assert msg.data == {}

    def test_connection_init_missing_type(self):
        """Should reject message without type field"""
        with pytest.raises(ValidationError) as exc_info:
            ConnectionInitMessage(id="test-id")

        assert "type" in str(exc_info.value)


class TestGameStateUpdateMessage:
    """Tests for GameStateUpdateMessage model"""

    def test_valid_game_state_message(self):
        """Should accept valid game_state_update message"""
        msg = GameStateUpdateMessage(
            type="game_state_update",
            id="state-123",
            data={
                "position": {"x": 100, "y": 64, "z": 200},
                "health": 20.0,
                "world": "minecraft:overworld",
            },
        )

        assert msg.type == "game_state_update"
        assert msg.data["position"]["x"] == 100
        assert msg.data["health"] == 20.0

    def test_game_state_with_empty_data(self):
        """Should accept message with empty data dict"""
        msg = GameStateUpdateMessage(type="game_state_update", data={})

        assert msg.type == "game_state_update"
        assert msg.data == {}

    def test_game_state_missing_data(self):
        """Should reject message without data field"""
        with pytest.raises(ValidationError) as exc_info:
            GameStateUpdateMessage(type="game_state_update")

        assert "data" in str(exc_info.value)

    def test_game_state_invalid_data_type(self):
        """Should reject message with non-dict data"""
        with pytest.raises(ValidationError) as exc_info:
            GameStateUpdateMessage(type="game_state_update", data="not-a-dict")

        # Pydantic V2 returns default error message for type validation
        error_str = str(exc_info.value)
        assert "data" in error_str
        assert ("dict" in error_str.lower() or "dictionary" in error_str.lower())


class TestConversationRequestMessage:
    """Tests for ConversationRequestMessage model"""

    def test_valid_conversation_request_full(self):
        """Should accept conversation_request with all optional fields"""
        msg = ConversationRequestMessage(
            type="conversation_request",
            id="conv-123",
            playerName="Steve",
            message="Hello, companion!",
            companionName="Alex",
            action=[{"type": "wave"}],
            timestamp="2025-12-05T10:00:00Z",
            position={"x": 100, "y": 64, "z": 200},
            health=18.5,
        )

        assert msg.type == "conversation_request"
        assert msg.playerName == "Steve"
        assert msg.message == "Hello, companion!"
        assert msg.health == 18.5

    def test_conversation_request_minimal(self):
        """Should accept conversation_request with only type"""
        msg = ConversationRequestMessage(type="conversation_request")

        assert msg.type == "conversation_request"
        assert msg.playerName is None
        assert msg.message is None

    def test_conversation_request_player_name_too_long(self):
        """Should reject playerName exceeding max_length=100"""
        with pytest.raises(ValidationError) as exc_info:
            ConversationRequestMessage(
                type="conversation_request", playerName="A" * 101
            )

        assert "playerName" in str(exc_info.value)
        assert "100" in str(exc_info.value)

    def test_conversation_request_message_too_long(self):
        """Should reject message exceeding max_length=1000"""
        with pytest.raises(ValidationError) as exc_info:
            ConversationRequestMessage(
                type="conversation_request", message="X" * 1001
            )

        assert "message" in str(exc_info.value)
        assert "1000" in str(exc_info.value)

    def test_conversation_request_player_name_empty_string(self):
        """Should reject playerName with empty string (min_length=1)"""
        with pytest.raises(ValidationError) as exc_info:
            ConversationRequestMessage(type="conversation_request", playerName="")

        assert "playerName" in str(exc_info.value)


class TestModMessage:
    """Tests for ModMessage (unified message model)"""

    def test_valid_mod_message_connection_init(self):
        """Should accept valid connection_init type"""
        msg = ModMessage(
            type="connection_init", id="mod-123", data={"version": "1.0"}
        )

        assert msg.type == "connection_init"
        assert msg.data == {"version": "1.0"}

    def test_valid_mod_message_game_state(self):
        """Should accept valid game_state_update type"""
        msg = ModMessage(
            type="game_state_update", data={"position": {"x": 0, "y": 0, "z": 0}}
        )

        assert msg.type == "game_state_update"

    def test_valid_mod_message_conversation_request(self):
        """Should accept valid conversation_request type with extra fields"""
        msg = ModMessage(
            type="conversation_request",
            playerName="Steve",
            message="Test message",
            companionName="Alex",
        )

        assert msg.type == "conversation_request"
        assert msg.playerName == "Steve"
        assert msg.message == "Test message"

    def test_mod_message_invalid_type(self):
        """Should reject invalid message type"""
        with pytest.raises(ValidationError) as exc_info:
            ModMessage(type="invalid_type")

        # Pydantic V2 Literal validation returns default error
        error_str = str(exc_info.value)
        assert "type" in error_str
        assert "literal_error" in error_str.lower() or "input should be" in error_str.lower()


class TestMonitorCommand:
    """Tests for MonitorCommand model"""

    def test_valid_monitor_command_clear_history(self):
        """Should accept valid clear_history command"""
        cmd = MonitorCommand(type="clear_history")

        assert cmd.type == "clear_history"

    def test_valid_monitor_command_reset_stats(self):
        """Should accept valid reset_stats command"""
        cmd = MonitorCommand(type="reset_stats")

        assert cmd.type == "reset_stats"

    def test_monitor_command_invalid_type(self):
        """Should reject invalid command type"""
        with pytest.raises(ValidationError) as exc_info:
            MonitorCommand(type="invalid_command")

        # Pydantic V2 Literal validation returns default error
        error_str = str(exc_info.value)
        assert "type" in error_str
        assert "literal_error" in error_str.lower() or "input should be" in error_str.lower()
