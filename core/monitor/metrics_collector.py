"""监控指标收集器：现在只做组合，具体逻辑拆分到独立类。"""

from __future__ import annotations

from core.monitor.message_stats import MessageStatsCollector
from core.monitor.connection_tracker import ConnectionTracker
from core.monitor.token_usage import TokenUsageTracker
from models.monitor import MessageStats, ConnectionStatus, TokenTrendStats


class MetricsCollector:
    """组合模式：聚合消息统计、连接状态、Token 趋势。"""

    def __init__(self) -> None:
        self.message_stats = MessageStatsCollector()
        self.connection_tracker = ConnectionTracker()
        self.token_usage = TokenUsageTracker()

    # 兼容旧接口 —— 直接委派
    def record_message_received(self, message_type: str) -> None:
        self.message_stats.record_received(message_type)

    def record_message_sent(self, message_type: str) -> None:
        self.message_stats.record_sent(message_type)

    def set_mod_connected(self, client_id: str) -> None:
        self.connection_tracker.set_mod_connected(client_id)

    def set_mod_disconnected(self) -> None:
        self.connection_tracker.set_mod_disconnected()

    def update_mod_last_message(self) -> None:
        self.connection_tracker.update_mod_last_message()

    def set_llm_status(self, provider: str, ready: bool) -> None:
        self.connection_tracker.set_llm_status(provider, ready)

    def get_stats(self) -> MessageStats:
        return self.message_stats.get_stats()

    def get_connection_status(self) -> ConnectionStatus:
        return self.connection_tracker.get_status()

    def record_token_usage(self, tokens: int) -> None:
        self.token_usage.record(tokens)

    def get_token_trend(self) -> TokenTrendStats:
        return self.token_usage.get_trend()

    def reset_stats(self) -> None:
        self.message_stats.reset()
