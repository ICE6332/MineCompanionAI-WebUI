"""Token 趋势统计。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict

from models.monitor import TokenTrendStats, TokenTrendPoint


class TokenUsageTracker:
    """仅负责 token 趋势累积与查询。"""

    def __init__(self) -> None:
        self._trend: Dict[str, int] = {}

    def record(self, tokens: int) -> None:
        now = datetime.now(timezone.utc)
        hour_key = now.strftime("%Y-%m-%d %H:00")
        self._trend[hour_key] = self._trend.get(hour_key, 0) + tokens

        cutoff = now - timedelta(hours=24)
        outdated_keys = [
            key
            for key in list(self._trend.keys())
            if datetime.strptime(key, "%Y-%m-%d %H:00").replace(tzinfo=timezone.utc) < cutoff
        ]
        for key in outdated_keys:
            del self._trend[key]

    def get_trend(self) -> TokenTrendStats:
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

        trend_points = []
        total_tokens = 0

        for offset in range(23, -1, -1):
            hour_dt = now - timedelta(hours=offset)
            hour_key = hour_dt.strftime("%Y-%m-%d %H:00")
            tokens = self._trend.get(hour_key, 0)
            total_tokens += tokens
            trend_points.append(
                TokenTrendPoint(
                    hour=hour_dt.strftime("%H:00"),
                    tokens=tokens,
                    timestamp=hour_dt,
                )
            )

        return TokenTrendStats(
            trend=trend_points,
            total_tokens=total_tokens,
            last_updated=now,
        )
