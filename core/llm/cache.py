"""LLM 缓存键生成工具。"""

from __future__ import annotations

import hashlib
import json
from typing import List, Dict, Any


def generate_cache_key(messages: List[Dict[str, Any]], model: str, temperature: float) -> str:
    """为 LLM 请求生成稳定的缓存键。"""
    payload = {
        "messages": messages,
        "model": model,
        "temperature": temperature,
    }
    content = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return f"llm:cache:{hashlib.sha256(content.encode()).hexdigest()}"
