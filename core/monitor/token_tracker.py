"""Token 统计工具。

提供简易 Token 计数与两种消息格式（标准/紧凑）的对比统计。
"""

import json
from typing import Any, Dict


class TokenTracker:
    @staticmethod
    def count_tokens(text: str) -> int:
        """简易 token 计数：按字符数/4 估算。

        说明：该估算用于对比不同消息格式的相对消耗，非精确计费口径。
        """
        return len(text) // 4

    @staticmethod
    def compare(standard_msg: Dict[str, Any], compact_msg: Dict[str, Any]) -> Dict[str, Any]:
        """对比两种格式的 token 消耗并返回统计结果。"""
        standard_json: str = json.dumps(standard_msg, ensure_ascii=False)
        compact_json: str = json.dumps(compact_msg, ensure_ascii=False)

        standard_tokens: int = TokenTracker.count_tokens(standard_json)
        compact_tokens: int = TokenTracker.count_tokens(compact_json)
        saved: int = standard_tokens - compact_tokens
        saved_percent: float = (saved / standard_tokens * 100) if standard_tokens > 0 else 0.0

        return {
            "standard_tokens": standard_tokens,
            "compact_tokens": compact_tokens,
            "saved_tokens": saved,
            "saved_percent": round(saved_percent, 1),
        }
