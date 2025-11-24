"""核心组件的抽象接口定义。

所有注释/文档面向开发者，保持中文；类型标识使用英文。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Protocol

from core.monitor.event_types import MonitorEventType
from models.monitor import ConnectionStatus, MessageStats, TokenTrendStats


class EventBusInterface(Protocol):
    """事件总线接口，用于发布与订阅监控事件。"""

    def publish(
        self,
        event_type: MonitorEventType,
        data: Dict[str, Any],
        severity: str = "info",
    ) -> None: ...

    def subscribe(
        self, event_type: MonitorEventType, callback: Callable[[Dict[str, Any]], None]
    ) -> None: ...

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]: ...

    def clear_history(self) -> None: ...


class MetricsInterface(Protocol):
    """监控指标接口，聚合消息/连接/令牌统计。"""

    def record_message_received(self, message_type: str) -> None: ...

    def record_message_sent(self, message_type: str) -> None: ...

    def set_mod_connected(self, client_id: str) -> None: ...

    def set_mod_disconnected(self) -> None: ...

    def update_mod_last_message(self) -> None: ...

    def set_llm_status(self, provider: str, ready: bool) -> None: ...

    def get_stats(self) -> MessageStats: ...

    def get_connection_status(self) -> ConnectionStatus: ...

    def record_token_usage(self, tokens: int) -> None: ...

    def get_token_trend(self) -> TokenTrendStats: ...

    def reset_stats(self) -> None: ...


class LLMServiceInterface(Protocol):
    """LLM 服务接口，封装 chat completion 能力。"""

    config: Dict[str, Any]

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]: ...


class ConnectionManagerInterface(Protocol):
    """WebSocket 连接管理接口，抽象活跃连接存取。"""

    def add(self, client_id: str, websocket: Any) -> None: ...

    def remove(self, client_id: str) -> None: ...

    def get(self, client_id: str) -> Any | None: ...

    def get_all_ids(self) -> list[str]: ...

    def count(self) -> int: ...


class ConversationContextInterface(Protocol):
    """会话上下文接口，管理游戏玩家的历史消息。"""

    def create_session(self, client_id: str, player_name: str): ...

    def add_message(
        self, client_id: str, role: str, content: str, player_name: Optional[str] = None
    ) -> None: ...

    def get_history(self, client_id: str) -> List[Dict[str, Any]]: ...

    def clear_session(self, client_id: str) -> None: ...

    def has_session(self, client_id: str) -> bool: ...
