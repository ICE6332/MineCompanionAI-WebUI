"""测试 LLM 缓存键生成。"""

import hashlib

from core.llm.cache import generate_cache_key


def test_generate_cache_key_stable():
    messages = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
    key1 = generate_cache_key(messages, "gpt-4", 0.7)
    key2 = generate_cache_key(messages, "gpt-4", 0.7)
    assert key1 == key2
    assert key1.startswith("llm:cache:")
    # 校验长度（sha256）
    assert len(key1.split(":")[-1]) == len(hashlib.sha256().hexdigest())


def test_generate_cache_key_diff_by_model():
    messages = [{"role": "user", "content": "hello"}]
    k1 = generate_cache_key(messages, "gpt-4", 0.7)
    k2 = generate_cache_key(messages, "gpt-3.5-turbo", 0.7)
    assert k1 != k2
