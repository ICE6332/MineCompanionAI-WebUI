"""监控系统相关的数据模型定义。"""

# 监控数据模型需要遵循 Pydantic v2 语法
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import uuid4

from pydantic import BaseModel, Field


class MonitorEvent(BaseModel):
    """监控事件模型"""

    # 事件唯一 ID
    id: str = Field(default_factory=lambda: str(uuid4()), description="事件唯一标识")
    # 事件类型
    type: str = Field(..., description="事件类型")
    # 时间戳使用 UTC 时间
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="事件时间戳（UTC）")
    # 附带的数据字典
    data: Dict[str, Any] = Field(..., description="事件数据")
    # 严重程度标识
    severity: str = Field(default="info", description="严重程度: info/warning/error")


class ConnectionStatus(BaseModel):
    """连接状态模型"""

    # 模组客户端 ID
    mod_client_id: Optional[str] = Field(default=None, description="模组客户端 ID")
    # 模组连接时间
    mod_connected_at: Optional[datetime] = Field(default=None, description="模组连接时间")
    # 模组最近一次消息时间
    mod_last_message_at: Optional[datetime] = Field(default=None, description="模组最近消息时间")
    # LLM 提供商
    llm_provider: Optional[str] = Field(default=None, description="LLM 提供商")
    # LLM 是否就绪
    llm_ready: bool = Field(default=False, description="LLM 是否就绪")


class MessageStats(BaseModel):
    """消息统计模型"""

    # 接收消息总数
    total_received: int = Field(default=0, description="接收消息总数")
    # 发送消息总数
    total_sent: int = Field(default=0, description="发送消息总数")
    # 按类型统计消息数量
    messages_per_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计的消息数量")
    # 最近一次重置时间
    last_reset_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="最近一次统计重置时间")


class TokenTrendPoint(BaseModel):
    """Token 消耗趋势单点模型"""

    # 小时标签（格式 HH:00）
    hour: str = Field(..., description="小时标签，格式 HH:00")
    # 该小时的 token 消耗
    tokens: int = Field(default=0, description="该小时的 token 消耗总数")
    # 时间戳（UTC）
    timestamp: datetime = Field(
        # 使用带 tzinfo 的 UTC 时间，保证序列化时附带 Z 后缀
        default_factory=lambda: datetime.now(timezone.utc),
        description="时间戳（UTC）",
    )


class TokenTrendStats(BaseModel):
    """Token 趋势统计模型"""

    # 最近 24 小时的趋势点列表
    trend: List[TokenTrendPoint] = Field(default_factory=list, description="最近 24 小时趋势")
    # 24 小时内的 token 总消耗
    total_tokens: int = Field(default=0, description="24 小时内总 token 消耗")
    # 最后更新时间（UTC）
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="最后更新时间",
    )


__all__ = [
    "MonitorEvent",
    "ConnectionStatus",
    "MessageStats",
    "TokenTrendPoint",
    "TokenTrendStats",
]
