"""测试配置加载。"""

from config.settings import settings


def test_settings_defaults():
    assert settings.storage_backend in ("memory", "redis")
    assert settings.llm_cache_ttl > 0
    assert settings.rate_limit_messages > 0
    assert settings.rate_limit_window > 0
