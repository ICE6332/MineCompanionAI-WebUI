"""处理 conversation_request 消息。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import WebSocket

from api.handlers.base import MessageHandler
from api.handlers.context import HandlerContext
from api.protocol import CompactProtocol
from core.monitor.event_types import MonitorEventType
from core.monitor.token_tracker import TokenTracker


logger = logging.getLogger("api.handlers.conversation")


class ConversationHandler(MessageHandler):
    async def handle(self, websocket: WebSocket, message: Dict[str, Any], context: HandlerContext) -> str:
        standard_message: Dict[str, Any] = CompactProtocol.parse(message)

        player_name: str = str(standard_message.get("playerName") or "玩家")
        player_message: str = str(standard_message.get("message", "") or "")
        message_id: str = str(standard_message.get("id", "") or "")
        companion_name: str = str(standard_message.get("companionName", "AICompanion") or "AICompanion")

        system_prompt = (
            f"你是 Minecraft 世界中的 AI 伙伴，名字叫 {companion_name}。"
            "请用亲切、简洁的中文回答玩家，并在合适时提供实用的生存建议。"
        )
        history_entries = context.conversation_context.get_history(context.client_id)
        history_messages = [
            {"role": entry.get("role", "user"), "content": str(entry.get("content", ""))}
            for entry in history_entries
        ]
        current_user_message = {"role": "user", "content": f"[{player_name}] {player_message}"}
        llm_messages = [{"role": "system", "content": system_prompt}, *history_messages, current_user_message]

        default_reply = "抱歉，我暂时无法响应，请稍后再试。"
        reply: str = default_reply

        context.event_bus.publish(
            MonitorEventType.LLM_REQUEST,
            {
                "client_id": context.client_id,
                "message_type": "conversation_request",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "preview": player_message[:200],
            },
        )

        # 先记录用户消息，确保断线重试时可还原上下文
        context.conversation_context.add_message(
            context.client_id,
            role="user",
            content=current_user_message["content"],
            player_name=player_name,
        )

        try:
            # 对话场景禁用缓存，避免相同问题返回旧答案
            llm_response = await context.llm_service.chat_completion(
                messages=llm_messages,
                use_cache=False
            )
            choices = llm_response.get("choices", [])
            first_choice = choices[0] if choices else {}
            if isinstance(first_choice, dict):
                message_obj = first_choice.get("message", {})
            else:
                message_obj = {}
            llm_reply = message_obj.get("content", "")
            if isinstance(llm_reply, str):
                reply = llm_reply.strip() or default_reply
            else:
                reply = str(llm_reply)

            context.conversation_context.add_message(
                context.client_id,
                role="assistant",
                content=reply,
            )

            context.event_bus.publish(
                MonitorEventType.LLM_RESPONSE,
                {
                    "client_id": context.client_id,
                    "message_type": "conversation_response",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "preview": reply[:200],
                    "usage": llm_response.get("usage"),
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("LLM 调用失败: client=%s, message=%s", context.client_id, message_id)
            context.event_bus.publish(
                MonitorEventType.LLM_ERROR,
                {
                    "client_id": context.client_id,
                    "message_type": "conversation_request",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": str(exc),
                },
            )
            context.conversation_context.add_message(
                context.client_id,
                role="assistant",
                content=reply,
            )

        standard_response: Dict[str, Any] = {
            "id": message_id,
            "type": "conversation_response",
            "companionName": companion_name,
            "message": reply,
        }

        compact_response: Dict[str, Any] = CompactProtocol.compact(standard_response)

        stats: Dict[str, Any] = TokenTracker.compare(standard_response, compact_response)
        stats["client_id"] = context.client_id
        stats["message_type"] = "conversation"

        context.metrics.record_message_sent("conversation_response")
        context.metrics.record_token_usage(stats["compact_tokens"])

        context.event_bus.publish(MonitorEventType.TOKEN_STATS, stats)
        context.event_bus.publish(
            MonitorEventType.MESSAGE_SENT,
            {
                "client_id": context.client_id,
                "message_type": "conversation_response",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        await websocket.send_json(standard_response)
        return json.dumps(standard_response)
