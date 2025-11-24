"""消息统计收集器。"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict

from models.monitor import MessageStats


class MessageStatsCollector:
    """仅负责消息收集与查询。"""

    def __init__(self) -> None:
        self._stats = MessageStats(
            total_received=0,
            total_sent=0,
            messages_per_type={},
            last_reset_at=datetime.now(timezone.utc),
        )
        self._stats.messages_per_type = defaultdict(int)

    def record_received(self, message_type: str) -> None:
        self._stats.total_received += 1
        self._stats.messages_per_type[message_type] += 1

    def record_sent(self, message_type: str) -> None:
        self._stats.total_sent += 1
        self._stats.messages_per_type[message_type] += 1

    def get_stats(self) -> MessageStats:
        return self._stats

    def reset(self) -> None:
        self._stats = MessageStats(
            total_received=0,
            total_sent=0,
            messages_per_type={},
            last_reset_at=datetime.now(timezone.utc),
        )
        self._stats.messages_per_type = defaultdict(int)
