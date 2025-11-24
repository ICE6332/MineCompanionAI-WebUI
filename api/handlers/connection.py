"""处理 connection_init 消息。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import WebSocket

from api.handlers.base import MessageHandler
from api.handlers.context import HandlerContext
from core.monitor.event_types import MonitorEventType


class ConnectionInitHandler(MessageHandler):
    async def handle(self, websocket: WebSocket, message: Dict[str, Any], context: HandlerContext) -> str:
        response = {
            "type": "connection_ack",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"client_id": context.client_id},
        }
        await websocket.send_json(response)

        context.metrics.record_message_sent("connection_ack")
        context.event_bus.publish(
            MonitorEventType.MESSAGE_SENT,
            {
                "client_id": context.client_id,
                "message_type": "connection_ack",
                "timestamp": response["timestamp"],
            },
        )

        return json.dumps(response)
