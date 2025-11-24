from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime, timezone


class WebSocketMessage(BaseModel):
    """WebSocket 消息基础模型"""

    id: str = Field(..., description="消息唯一标识")
    type: str = Field(..., description="消息类型")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="时间戳"
    )
    data: dict[str, Any] = Field(..., description="消息数据")


class GameStateUpdate(BaseModel):
    """游戏状态更新消息"""

    type: str = Field(default="game_state_update")
    data: dict[str, Any]


class ActionCommand(BaseModel):
    """AI 行为指令"""

    type: str = Field(default="action_command")
    data: dict[str, Any]


class ConversationRequest(BaseModel):
    """对话请求"""

    type: str = Field(default="conversation_request")
    data: dict[str, Any]


class ConversationResponse(BaseModel):
    """对话响应"""

    type: str = Field(default="conversation_response")
    data: dict[str, Any]


class ErrorMessage(BaseModel):
    """错误消息"""

    type: str = Field(default="error")
    data: dict[str, Any] = Field(..., description="包含 code, message, details")
