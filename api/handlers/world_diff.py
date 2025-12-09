"""处理 world_diff 消息。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, cast

import orjson
from fastapi import WebSocket

from api.handlers.base import MessageHandler
from api.handlers.context import HandlerContext
from core.interfaces import EngineSessionInterface
from core.monitor.event_types import MonitorEventType

logger = logging.getLogger("api.handlers.world_diff")


class WorldDiffHandler(MessageHandler):
    """将世界增量同步到引擎并回传动作。"""

    async def handle(
        self, websocket: WebSocket, message: Dict[str, Any], context: HandlerContext
    ) -> str:
        session_id = str(message.get("session_id") or message.get("sessionId") or "")
        diff = message.get("data") or {}

        engine_manager = context.engine_manager
        if engine_manager is None:
            return await self._send_error(
                websocket,
                context,
                "engine_disabled",
                "引擎功能未启用",
            )

        session = engine_manager.get(session_id)
        if session is None:
            return await self._send_error(
                websocket,
                context,
                "session_not_found",
                "未找到对应会话",
            )

        # Type assertion for Protocol type narrowing
        session = cast(EngineSessionInterface, session)

        runtime = getattr(engine_manager, "runtime", None)
        vision_store = getattr(engine_manager, "vision_store", None)
        story_store = getattr(engine_manager, "story_store", None)
        if runtime is None or vision_store is None or story_store is None:
            return await self._send_error(
                websocket,
                context,
                "engine_disabled",
                "引擎依赖未初始化",
            )

        try:
            outputs = await session.on_world_diff(
                runtime, vision_store, story_store, diff
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "world_diff 处理失败: client=%s, session=%s",
                context.client_id,
                session_id,
            )
            return await self._send_error(
                websocket,
                context,
                "world_diff_failed",
                str(exc),
            )

        previews: List[str] = []
        for output in outputs:
            msg_type = str(output.get("type", "unknown"))
            payload = {**output}
            payload.setdefault("session_id", session_id)

            serialized = orjson.dumps(payload).decode("utf-8")
            await websocket.send_text(serialized)
            self._record_send(context, msg_type)
            previews.append(serialized)

        return previews[-1] if previews else ""

    async def _send_error(
        self,
        websocket: WebSocket,
        context: HandlerContext,
        code: str,
        message: str,
    ) -> str:
        """封装错误下行逻辑。"""
        payload = {
            "type": "error",
            "code": code,
            "message": message,
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
