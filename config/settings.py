"""应用配置，便于按环境切换存储与缓存。"""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置"""

    # 存储配置
    storage_backend: Literal["memory", "redis"] = "memory"
    redis_url: str = "redis://localhost:6379"

    # LLM 配置（新增）
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    llm_api_key: str = ""
    llm_base_url: str = ""

    # LLM 缓存配置
    llm_cache_enabled: bool = True
    llm_cache_ttl: int = 3600  # 秒

    # 监控配置
    event_history_size: int = 100
    rate_limit_messages: int = 100
    rate_limit_window: int = 60

    # 日志配置（新增）
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
