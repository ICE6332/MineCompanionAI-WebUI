"""监控事件总线实现。"""

from typing import Dict, List, Callable, Any
from collections import deque
from datetime import datetime, timezone
from core.monitor.event_types import MonitorEventType
import uuid


class EventBus:
    """负责事件分发与记录的实例化事件总线。"""

    def __init__(self, history_size: int = 100) -> None:
        self._subscribers: Dict[MonitorEventType, List[Callable[[Dict[str, Any]], None]]] = {}
        self._event_history: deque = deque(maxlen=history_size)

    def publish(
        self,
        event_type: MonitorEventType,
        data: Dict[str, Any],
        severity: str = "info",
    ) -> None:
        """发布事件并通知订阅者。"""
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type.value,
            # 使用带时区的 UTC 时间
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
            "severity": severity,
        }

        self._event_history.append(event)

        for callback in self._subscribers.get(event_type, []):
            callback(event)

    def subscribe(
        self, event_type: MonitorEventType, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """订阅指定类型事件。"""
        self._subscribers.setdefault(event_type, []).append(callback)

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """返回最近的事件记录。"""
        if limit <= 0:
            return []
        events = list(self._event_history)
        return events[-limit:]

    def clear_history(self) -> None:
        """清空事件历史。"""
        self._event_history.clear()
