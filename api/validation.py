"""WebSocket 消息验证模型"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, validator


class ModMessageBase(BaseModel):
    """模组消息基础模型"""

    id: Optional[str] = None


class ConnectionInitMessage(ModMessageBase):
    """连接初始化消息"""

    type: Literal["connection_init"]
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GameStateUpdateMessage(ModMessageBase):
    """游戏状态更新消息"""

    type: Literal["game_state_update"]
    data: Dict[str, Any] = Field(..., description="游戏状态数据")

    @validator("data")
    def validate_game_state(cls, v):
        """验证游戏状态数据"""
        if not isinstance(v, dict):
            raise ValueError("data 必须是字典类型")
        return v


class ConversationRequestMessage(ModMessageBase):
    """对话请求消息"""

    type: Literal["conversation_request"]
    playerName: Optional[str] = Field(None, min_length=1, max_length=100)
    message: Optional[str] = Field(None, max_length=1000)
    companionName: Optional[str] = None
    action: Optional[List[Dict[str, Any]]] = None
    timestamp: Optional[str] = None
    position: Optional[Dict[str, Any]] = None
    health: Optional[float] = None


class ModMessage(BaseModel):
    """通用模组消息（用于 /api/ws/send-json）"""

    type: Literal["connection_init", "game_state_update", "conversation_request"]
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    id: Optional[str] = None

    # conversation_request 特有字段
    playerName: Optional[str] = Field(None, min_length=1, max_length=100)
    message: Optional[str] = Field(None, max_length=1000)
    companionName: Optional[str] = None
    action: Optional[List[Dict[str, Any]]] = None
    timestamp: Optional[str] = None
    position: Optional[Dict[str, Any]] = None
    health: Optional[float] = None

    @validator("type")
    def validate_type(cls, v):
        """验证消息类型"""
        allowed = ["connection_init", "game_state_update", "conversation_request"]
        if v not in allowed:
            raise ValueError(f"消息类型必须是以下之一: {allowed}")
        return v


class MonitorCommand(BaseModel):
    """监控WebSocket命令"""

    type: Literal["clear_history", "reset_stats"]

    @validator("type")
    def validate_command_type(cls, v):
        """验证命令类型"""
        allowed = ["clear_history", "reset_stats"]
        if v not in allowed:
            raise ValueError(f"命令类型必须是以下之一: {allowed}")
        return v
