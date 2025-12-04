"""处理 engine_init 消息。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

import orjson
from fastapi import WebSocket

from api.handlers.base import MessageHandler
from api.handlers.context import HandlerContext
from core.monitor.event_types import MonitorEventType

logger = logging.getLogger("api.handlers.engine_init")


class EngineInitHandler(MessageHandler):
    """初始化引擎会话。"""

    async def handle(self, websocket: WebSocket, message: Dict[str, Any], context: HandlerContext) -> str:
        session_id = str(message.get("session_id") or message.get("sessionId") or "")
        character_id = str(message.get("character_id") or message.get("characterId") or "")
        character_card = message.get("character_card") or message.get("characterCard") or {}
        config = message.get("config") or {}

        engine_manager = context.engine_manager
        if engine_manager is None:
            payload = {
                "type": "error",
                "code": "engine_disabled",
                "message": "引擎功能未启用",
            }
            serialized = orjson.dumps(payload).decode("utf-8")
            await websocket.send_text(serialized)
            self._record_send(context, payload["type"])
            return serialized

        try:
            session = await engine_manager.get_or_create(
                session_id=session_id,
                character_id=character_id,
                character_card=character_card,
                config=config,
            )
            response = {
                "type": "engine_ready",
                "session_id": session.session_id,
            }
            serialized = orjson.dumps(response).decode("utf-8")
            await websocket.send_text(serialized)
            self._record_send(context, response["type"])
            return serialized
        except Exception as exc:  # noqa: BLE001
            logger.exception("引擎初始化失败: client=%s, session=%s", context.client_id, session_id)
            payload = {
                "type": "error",
                "code": "init_failed",
                "message": str(exc),
            }
            serialized = orjson.dumps(payload).decode("utf-8")
            await websocket.send_text(serialized)
            self._record_send(context, payload["type"])
            return serialized

    def _record_send(self, context: HandlerContext, message_type: str) -> None:
        """记录监控事件与指标。"""
        context.metrics.record_message_sent(message_type)
        context.event_bus.publish(
            MonitorEventType.MESSAGE_SENT,
            {
                "client_id": context.client_id,
                "message_type": message_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
