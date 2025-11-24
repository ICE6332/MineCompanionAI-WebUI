"""消息处理器协议定义。"""

from __future__ import annotations

from typing import Protocol, Dict, Any
from fastapi import WebSocket

from api.handlers.context import HandlerContext


class MessageHandler(Protocol):
    """消息处理器接口。"""

    async def handle(self, websocket: WebSocket, message: Dict[str, Any], context: HandlerContext) -> str:
        """
        处理消息并返回响应预览字符串。
        """
        ...
