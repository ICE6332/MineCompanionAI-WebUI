import json
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any, Dict

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from core.monitor.event_types import MonitorEventType
from api.protocol import CompactProtocol
from api.validation import ModMessage
from api.rate_limiter import WebSocketRateLimiter
from core.monitor.token_tracker import TokenTracker
from core.dependencies import (
    EventBusDep,
    MetricsDep,
    ConnectionManagerDep,
    LLMDep,
    ConversationContextDep,
)
from config.settings import settings
from api.handlers.registry import get_handler
from api.handlers.context import HandlerContext

router = APIRouter()
logger = logging.getLogger("api.websocket")

# WebSocket 速率限制器（配置驱动）
mod_rate_limiter = WebSocketRateLimiter(
    max_messages=settings.rate_limit_messages, window_seconds=settings.rate_limit_window
)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    event_bus: EventBusDep,
    metrics: MetricsDep,
    conn_mgr: ConnectionManagerDep,
    llm_service: LLMDep,
    conversation_context: ConversationContextDep,
):
    """
    WebSocket 端点
    当前实现：解析模组消息并触发监控事件
    TODO: 集成 LLM、记忆系统、决策引擎
    """
    client_id = f"mod-{uuid4()}"
    await websocket.accept()
    conn_mgr.add(client_id, websocket)
    logger.info("[OK] Client connected: %s", client_id)
    connection_timestamp = datetime.now(timezone.utc).isoformat()
    event_bus.publish(
        MonitorEventType.MOD_CONNECTED,
        {"client_id": client_id, "timestamp": connection_timestamp},
    )
    metrics.set_mod_connected(client_id)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            # 检查速率限制
            if not mod_rate_limiter.check_rate_limit(client_id):
                error_response = {
                    "type": "error",
                    "data": {"message": "消息发送过快，请稍后再试（限制：100条/分钟）"},
                }
                await websocket.send_json(error_response)
                continue  # 跳过此消息，但不断开连接

            logger.debug("← Received from %s: %s...", client_id, data[:100])
            try:
                # 解析来自 Mod 的 JSON 消息
                message = json.loads(data)
            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "data": {"message": "无法解析 JSON 数据"},
                }
                await websocket.send_json(error_response)
                logger.debug("→ Sent to %s: %s...", client_id, json.dumps(error_response)[:100])
                error_timestamp = datetime.now(timezone.utc).isoformat()
                event_bus.publish(
                    MonitorEventType.MESSAGE_RECEIVED,
                    {
                        "client_id": client_id,
                        "message_type": "invalid_json",
                        "timestamp": error_timestamp,
                        "preview": data[:100],
                    },
                )
                metrics.record_message_received("invalid_json")
                metrics.update_mod_last_message()
                metrics.record_message_sent("error")
                event_bus.publish(
                    MonitorEventType.MESSAGE_SENT,
                    {
                        "client_id": client_id,
                        "message_type": "error",
                        "timestamp": error_timestamp,
                    },
                )
                continue

            # 预解析：统一紧凑/标准/旧版 data 结构，确保路由基于长类型值
            try:
                normalized_msg = CompactProtocol.parse(message)
            except Exception:
                error_payload = {
                    "type": "error",
                    "data": {"message": "无法解析协议字段"},
                }
                await websocket.send_json(error_payload)
                metrics.record_message_sent("error")
                event_bus.publish(
                    MonitorEventType.MESSAGE_SENT,
                    {
                        "client_id": client_id,
                        "message_type": "error",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
                continue

            msg_type = normalized_msg.get("type", "unknown")
            timestamp = datetime.now(timezone.utc).isoformat()
            preview = data[:100]
            event_bus.publish(
                MonitorEventType.MESSAGE_RECEIVED,
                {
                    "client_id": client_id,
                    "message_type": msg_type,
                    "timestamp": timestamp,
                    "preview": preview,
                },
            )
            metrics.record_message_received(msg_type)
            metrics.update_mod_last_message()

            handler = get_handler(msg_type)
            context = HandlerContext(
                client_id=client_id,
                event_bus=event_bus,
                metrics=metrics,
                llm_service=llm_service,
                conversation_context=conversation_context,
            )
            response_preview = None
            if handler:
                response_preview = await handler.handle(websocket, normalized_msg, context)
            else:
                error_payload = {
                    "type": "error",
                    "data": {
                        "message": f"未知消息类型: {msg_type}",
                        "client_id": client_id,
                    },
                }
                await websocket.send_json(error_payload)
                response_preview = json.dumps(error_payload)
                metrics.record_message_sent("error")
                event_bus.publish(
                    MonitorEventType.MESSAGE_SENT,
                    {
                        "client_id": client_id,
                        "message_type": "error",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )

            if response_preview:
                logger.debug("→ Sent to %s: %s...", client_id, response_preview[:100])

    except WebSocketDisconnect:
        logger.warning("[ERR] Client disconnected: %s", client_id)
        event_bus.publish(
            MonitorEventType.MOD_DISCONNECTED,
            {"client_id": client_id, "timestamp": datetime.now(timezone.utc).isoformat()},
        )
        metrics.set_mod_disconnected()
    except Exception as e:
        logger.error("[ERR] WebSocket error for %s: %s", client_id, e)
    finally:
        mod_rate_limiter.clear(client_id)
        conn_mgr.remove(client_id)




@router.post("/api/ws/send-json")
async def send_json_to_mod(
    message: ModMessage,
    event_bus: EventBusDep,
    metrics: MetricsDep,
    conn_mgr: ConnectionManagerDep,
):
    """
    从 Web UI 转发原始 JSON 消息到当前已连接的模组。
    主要用于开发阶段临时调试通信链路。
    """
    if conn_mgr.count() == 0:
        raise HTTPException(status_code=503, detail="当前没有任何模组通过 WebSocket 连接")

    # 优先使用 MetricsCollector 记录的模组连接 ID
    connection_status = metrics.get_connection_status()
    target_id = connection_status.mod_client_id

    if not target_id or not conn_mgr.get(target_id):
        # 回退：选择任意一个活跃连接
        ids = conn_mgr.get_all_ids()
        target_id = ids[0] if ids else None

    if not target_id:
        raise HTTPException(status_code=503, detail="找不到可用的模组连接")

    websocket = conn_mgr.get(target_id)
    if websocket is None:
        raise HTTPException(status_code=503, detail="模组连接已失效，请重新连接后重试")

    # 将前端提供的 JSON 原样下发给模组（已通过 Pydantic 验证）
    await websocket.send_json(message.model_dump(exclude_none=True))

    msg_type = message.type
    metrics.record_message_sent(msg_type)
    event_bus.publish(
        MonitorEventType.MESSAGE_SENT,
        {
            "client_id": target_id,
            "message_type": msg_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    return {"status": "ok", "target": target_id, "type": msg_type}
