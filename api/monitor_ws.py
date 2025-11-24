"""监控 WebSocket 端点，用于将事件推送至前端"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json
from uuid import uuid4
import logging

from core.monitor.event_types import MonitorEventType
from api.validation import MonitorCommand
from api.rate_limiter import WebSocketRateLimiter
from core.dependencies import EventBusDep, MetricsDep

router = APIRouter()
logger = logging.getLogger("api.monitor_ws")

# 活跃监控客户端集合，避免重复推送
active_monitor_clients: Set[WebSocket] = set()

# 监控 WebSocket 速率限制器（每分钟最多 30 条命令）
monitor_rate_limiter = WebSocketRateLimiter(max_messages=30, window_seconds=60)


@router.websocket('/ws/monitor')
async def monitor_websocket(
    websocket: WebSocket,
    event_bus: EventBusDep,
    metrics: MetricsDep,
) -> None:
    '''
    前端监控专用 WebSocket 端点
    实时推送监控事件到前端
    '''

    await websocket.accept()
    client_id = f'monitor-{uuid4()}'
    active_monitor_clients.add(websocket)

    # 控制台提示连接状态
    logger.info('[OK] Monitor client connected: %s', client_id)

    # 发布前端连接事件，便于后端感知监听器变化
    event_bus.publish(MonitorEventType.FRONTEND_CONNECTED, {'client_id': client_id})

    # 发送历史事件，方便前端初始化状态
    history = event_bus.get_recent_events(limit=50)
    await websocket.send_json({
        'type': 'history',
        'events': history
    })

    # 发送当前统计信息，确保前端展示一致
    stats = metrics.get_stats()
    connection_status = metrics.get_connection_status()
    await websocket.send_json({
        'type': 'stats',
        'data': {
            'stats': stats.model_dump(mode='json'),
            'connection_status': connection_status.model_dump(mode='json')
        }
    })

    try:
        while True:
            # 接收前端发来的控制指令
            data = await websocket.receive_text()
            
            # 检查速率限制
            if not monitor_rate_limiter.check_rate_limit(client_id):
                await websocket.send_json({
                    'type': 'error', 
                    'message': '命令发送过快，请稍后再试（限制：30条/分钟）'
                })
                continue

            try:
                command_dict = json.loads(data)
                # 使用 Pydantic 验证命令
                validated_cmd = MonitorCommand(**command_dict)
                command_type = validated_cmd.type
            except json.JSONDecodeError:
                await websocket.send_json({'type': 'error', 'message': '无效指令格式'})
                continue
            except Exception as e:
                # Pydantic 验证失败
                await websocket.send_json({
                    'type': 'error', 
                    'message': f'无效的命令: {str(e)}'
                })
                continue

            # 根据指令类型执行不同管理操作
            if command_type == 'clear_history':
                event_bus.clear_history()
                await websocket.send_json({'type': 'ack', 'message': '历史记录已清除'})
            elif command_type == 'reset_stats':
                metrics.reset_stats()
                await websocket.send_json({'type': 'ack', 'message': '统计数据已重置'})

    except WebSocketDisconnect:
        logger.warning('[ERR] Monitor client disconnected: %s', client_id)
    except Exception as exc:  # noqa: BLE001
        # 捕获所有异常，避免协程静默失败
        logger.error('[ERR] Monitor WebSocket error: %s', exc)
    finally:
        # 清理客户端状态并通知事件总线
        monitor_rate_limiter.clear(client_id)
        active_monitor_clients.discard(websocket)
        event_bus.publish(MonitorEventType.FRONTEND_DISCONNECTED, {'client_id': client_id})


async def broadcast_event_to_monitors(event: Dict) -> None:
    '''广播事件到所有监控客户端'''
    disconnected: Set[WebSocket] = set()

    # 向所有在线监控客户端推送事件
    for client in list(active_monitor_clients):
        try:
            await client.send_json({
                'type': 'event',
                'event': event
            })
        except Exception:
            disconnected.add(client)

    # 清理断开连接的客户端，防止集合膨胀
    for client in disconnected:
        active_monitor_clients.discard(client)


def register_monitor_subscriptions(event_bus) -> None:
    """在应用启动时注册事件总线订阅，将事件转发给前端监控连接。"""
    for event_type in MonitorEventType:
        event_bus.subscribe(event_type, lambda event: asyncio.create_task(broadcast_event_to_monitors(event)))
