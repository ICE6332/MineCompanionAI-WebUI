"""消息处理器注册表。"""

from api.handlers.connection import ConnectionInitHandler
from api.handlers.conversation import ConversationHandler
from api.handlers.engine_init import EngineInitHandler
from api.handlers.game_state import GameStateHandler
from api.handlers.player_lifecycle import (
    PlayerConnectedHandler,
    PlayerDisconnectedHandler,
)
from api.handlers.player_message import PlayerMessageHandler
from api.handlers.world_diff import WorldDiffHandler

MESSAGE_HANDLERS = {
    "connection_init": ConnectionInitHandler(),
    "game_state_update": GameStateHandler(),
    "conversation_request": ConversationHandler(),
    "player_connected": PlayerConnectedHandler(),
    "player_disconnected": PlayerDisconnectedHandler(),
    "engine_init": EngineInitHandler(),
    "world_diff": WorldDiffHandler(),
    "player_message": PlayerMessageHandler(),
}


def get_handler(message_type: str):
    """根据消息类型获取处理器。"""
    return MESSAGE_HANDLERS.get(message_type)
