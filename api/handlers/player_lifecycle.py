"""处理玩家连接/离线生命周期事件。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import WebSocket

from api.handlers.base import MessageHandler
from api.handlers.context import HandlerContext
from core.monitor.event_types import MonitorEventType

logger = logging.getLogger("api.handlers.player_lifecycle")


class PlayerConnectedHandler(MessageHandler):
    async def handle(self, websocket: WebSocket, message: Dict[str, Any], context: HandlerContext) -> str:
        player_name = str(message.get("playerName") or "玩家")
        session = context.conversation_context.create_session(context.client_id, player_name)
        logger.info("玩家进入世界，已创建对话会话: client=%s, player=%s", context.client_id, player_name)

        response = {
            "type": "player_connected_ack",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "playerName": player_name,
            "sessionStartedAt": session.started_at.isoformat(),
        }
        await websocket.send_json(response)

        context.metrics.record_message_sent("player_connected_ack")
        context.event_bus.publish(
            MonitorEventType.MESSAGE_SENT,
            {
                "client_id": context.client_id,
                "message_type": "player_connected_ack",
                "timestamp": response["timestamp"],
            },
        )
        return json.dumps(response)


class PlayerDisconnectedHandler(MessageHandler):
    async def handle(self, websocket: WebSocket, message: Dict[str, Any], context: HandlerContext) -> str:
        player_name = str(message.get("playerName") or "玩家")
        context.conversation_context.clear_session(context.client_id)
        logger.info("玩家离开世界，已清空会话: client=%s, player=%s", context.client_id, player_name)

        response = {
            "type": "player_disconnected_ack",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "playerName": player_name,
        }
        await websocket.send_json(response)

        context.metrics.record_message_sent("player_disconnected_ack")
        context.event_bus.publish(
            MonitorEventType.MESSAGE_SENT,
            {
                "client_id": context.client_id,
                "message_type": "player_disconnected_ack",
                "timestamp": response["timestamp"],
            },
        )
        return json.dumps(response)
