"""WebSocket 速率限制器"""

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Dict


class WebSocketRateLimiter:
    """
    WebSocket 连接速率限制器

    使用滑动窗口算法限制消息发送频率，防止:
    - DoS 攻击
    - 资源耗尽
    - 意外的消息洪水
    """

    def __init__(self, max_messages: int = 100, window_seconds: int = 60):
        """
        初始化速率限制器

        Args:
            max_messages: 时间窗口内最大允许的消息数
            window_seconds: 时间窗口大小（秒）
        """
        self.max_messages = max_messages
        self.window = timedelta(seconds=window_seconds)
        self.message_times: Dict[str, deque] = defaultdict(deque)

    def check_rate_limit(self, client_id: str) -> bool:
        """
        检查客户端是否超过速率限制

        Args:
            client_id: 客户端唯一标识

        Returns:
            True 如果未超限，False 如果已超限
        """
        now = datetime.now(timezone.utc)

        # 清理超出时间窗口的旧记录
        while (
            self.message_times[client_id]
            and now - self.message_times[client_id][0] > self.window
        ):
            self.message_times[client_id].popleft()

        # 检查是否超过限制
        if len(self.message_times[client_id]) >= self.max_messages:
            return False

        # 记录本次消息时间
        self.message_times[client_id].append(now)
        return True

    def clear(self, client_id: str) -> None:
        """
        清除客户端的速率限制记录

        Args:
            client_id: 客户端唯一标识
        """
        self.message_times.pop(client_id, None)

    def get_remaining_quota(self, client_id: str) -> int:
        """
        获取客户端剩余配额

        Args:
            client_id: 客户端唯一标识

        Returns:
            剩余可发送的消息数量
        """
        now = datetime.now(timezone.utc)

        # 清理过期记录
        while (
            self.message_times[client_id]
            and now - self.message_times[client_id][0] > self.window
        ):
            self.message_times[client_id].popleft()

        used = len(self.message_times[client_id])
        return max(0, self.max_messages - used)
