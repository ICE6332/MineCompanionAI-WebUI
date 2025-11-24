"""WebSocket 连接管理器的最小实现。

首期用于替换散落的全局字典，后续可接入 Redis 等共享存储。
"""

from __future__ import annotations

import logging
from typing import Dict

from fastapi import WebSocket

from core.interfaces import ConnectionManagerInterface


logger = logging.getLogger(__name__)


class ConnectionManager(ConnectionManagerInterface):
    """在内存中管理活跃 WebSocket 连接。"""

    def __init__(self) -> None:
        self._connections: Dict[str, WebSocket] = {}

    def add(self, client_id: str, websocket: WebSocket) -> None:
        self._connections[client_id] = websocket

    def remove(self, client_id: str) -> None:
        self._connections.pop(client_id, None)

    def get(self, client_id: str) -> WebSocket | None:
        return self._connections.get(client_id)

    def get_all_ids(self) -> list[str]:
        return list(self._connections.keys())

    def count(self) -> int:
        return len(self._connections)

    async def close_all(self) -> None:
        """优雅关闭所有活跃连接。"""
        logger.info("正在关闭 %d 个活跃连接...", len(self._connections))
        for client_id, ws in list(self._connections.items()):
            try:
                await ws.close(code=1001, reason="服务端正在关闭")
                logger.debug("已关闭连接: %s", client_id)
            except Exception as err:  # noqa: BLE001
                logger.warning("关闭连接 %s 失败: %s", client_id, err)
        self._connections.clear()
        logger.info("所有连接已关闭")
