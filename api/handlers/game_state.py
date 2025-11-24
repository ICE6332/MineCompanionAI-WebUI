"""处理 game_state_update 消息。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import WebSocket

from api.handlers.base import MessageHandler
from api.handlers.context import HandlerContext
from core.monitor.event_types import MonitorEventType


class GameStateHandler(MessageHandler):
    async def handle(self, websocket: WebSocket, message: Dict[str, Any], context: HandlerContext) -> str:
        game_state = message.get("data", {})
        player_name = game_state.get("player_name", "Unknown")

        response = {
            "type": "game_state_ack",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"status": "received", "player": player_name},
        }
        await websocket.send_json(response)
        context.metrics.record_message_sent("game_state_ack")
        context.event_bus.publish(
            MonitorEventType.MESSAGE_SENT,
            {
                "client_id": context.client_id,
                "message_type": "game_state_ack",
                "timestamp": response["timestamp"],
            },
        )
        return json.dumps(response)
