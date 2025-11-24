"""LLM 服务核心实现。

使用 LiteLLM 统一接口，支持 OpenAI、Anthropic、Gemini 以及兼容 OpenAI 格式的第三方服务。
"""

import os
import json
import logging
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

import litellm

try:
    from litellm.exceptions import LiteLLMException
except Exception:  # noqa: BLE001
    LiteLLMException = Exception

from core.llm.cache import generate_cache_key
from core.storage.interfaces import CacheStorage
from config.settings import settings

# 加载环境变量
load_dotenv()

logger = logging.getLogger("core.llm.service")


class LLMService:
    """LLM 服务类，封装 LiteLLM 调用。"""

    def __init__(self, cache_storage: CacheStorage | None = None):
        self.config = self._load_config()
        self.cache = cache_storage
        self._setup_litellm()

    @staticmethod
    def _mask_api_key(api_key: Optional[str]) -> str:
        """仅暴露 API Key 前 8 位，避免日志泄露。"""
        if not api_key:
            return ""
        prefix = api_key[:8]
        return f"{prefix}***"

    @staticmethod
    def _response_to_dict(response: Any) -> Dict[str, Any]:
        """统一转成原生字典，便于后续缓存与序列化。"""
        if isinstance(response, dict):
            return response
        if isinstance(response, str):
            try:
                parsed = json.loads(response)
            except json.JSONDecodeError as exc:
                raise ValueError("响应字符串不是合法 JSON 数据") from exc
            if isinstance(parsed, dict):
                return parsed
            return {"data": parsed}
        if hasattr(response, "model_dump"):
            return response.model_dump()
        if hasattr(response, "dict"):
            return response.dict()
        if hasattr(response, "json"):
            try:
                raw_json = response.json()
                parsed = json.loads(raw_json) if isinstance(raw_json, str) else raw_json
                if isinstance(parsed, dict):
                    return parsed
                return {"data": parsed}
            except (TypeError, json.JSONDecodeError) as exc:
                raise ValueError("响应 json() 结果不是合法 JSON 数据") from exc
            except Exception as exc:  # noqa: BLE001
                raise ValueError("响应对象的 json() 方法执行失败") from exc
        # 最后尝试直接序列化，再解析回字典
        def _default_serializer(obj: Any) -> Any:
            if is_dataclass(obj):
                return asdict(obj)
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            raise TypeError(f"对象 {type(obj).__name__} 无法被序列化")

        try:
            serialized = json.dumps(response, default=_default_serializer)
            parsed = json.loads(serialized)
        except (TypeError, ValueError) as exc:
            raise ValueError("无法将响应序列化为 JSON") from exc
        if isinstance(parsed, dict):
            return parsed
        return {"data": parsed}

    def _load_config(self) -> Dict[str, Any]:
        """加载配置，优先使用环境变量，其次是 settings.json。"""
        settings_path = Path("config/settings.json")
        file_config = {}
        
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    file_config = data.get("llm", {})
            except Exception as e:
                logger.error(f"加载 settings.json 失败: {e}")

        # 环境变量优先级更高
        config = {
            "provider": os.getenv("LLM_PROVIDER", file_config.get("provider", "openai")),
            "model": os.getenv("LLM_MODEL", file_config.get("model", "gpt-4")),
            "api_key": os.getenv("LLM_API_KEY", file_config.get("api_key", "")),
            "base_url": os.getenv("LLM_BASE_URL", file_config.get("base_url", "")),
            "api_version": os.getenv("LLM_API_VERSION", file_config.get("api_version", "")),
        }
        
        return config

    def _setup_litellm(self):
        """配置 LiteLLM。"""
        # 设置 API Key
        if self.config["api_key"]:
            # LiteLLM 会自动查找环境变量，但这里显式设置更安全
            # 注意：不同 provider 需要不同的环境变量名，但 LiteLLM 支持通过参数传递 api_key
            pass
        
        # 配置日志
        litellm.set_verbose = False  # 设置为 True 可开启详细调试日志
        
        # 自动丢弃模型不支持的参数，避免 GPT-5 等模型报错
        litellm.drop_params = True
        logger.info("✅ LiteLLM 配置：自动丢弃不支持的参数 (drop_params=True)")

    def _resolve_request_url(self, provider: str, params: Dict[str, Any]) -> Optional[str]:
        """尝试推断真实的 HTTP 请求 URL。"""
        endpoint = self._guess_endpoint(provider, params)
        provider_lower = provider.lower()

        api_base = params.get("api_base") or self.config.get("base_url")
        if api_base:
            return self._compose_url(api_base, endpoint, provider_lower, params)

        default_bases = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "gemini": "https://generativelanguage.googleapis.com/v1beta",
        }
        base_candidate = default_bases.get(provider_lower)
        if base_candidate:
            return self._compose_url(base_candidate, endpoint, provider_lower, params)
        return None

    @staticmethod
    def _compose_url(
        base_url: str,
        endpoint: str,
        provider_lower: str,
        params: Dict[str, Any],
    ) -> str:
        normalized = base_url.rstrip("/")
        query = ""
        if provider_lower.startswith("azure") and "?" not in normalized:
            api_version = params.get("api_version")
            if api_version:
                query = f"?api-version={api_version}"
        return f"{normalized}/{endpoint}{query}"

    @staticmethod
    def _guess_endpoint(provider: str, params: Dict[str, Any]) -> str:
        provider_lower = provider.lower()
        if "anthropic" in provider_lower:
            return "messages"
        if provider_lower.startswith("azure"):
            return "chat/completions"
        if "gemini" in provider_lower or provider_lower == "google":
            model_name = params.get("model")
            if model_name:
                return f"models/{model_name}:generateContent"
            return "models:generateContent"
        if "ollama" in provider_lower:
            return "api/chat"
        return "chat/completions"

    def _log_http_debug_response(self, resp: Any, request_url: Optional[str]) -> None:
        """记录 HTTP 响应的调试信息，帮助定位解析失败问题。"""
        status_code = getattr(resp, "status_code", None)
        headers = getattr(resp, "headers", None)
        content_type: Optional[str] = None
        if headers and hasattr(headers, "get"):
            content_type = headers.get("Content-Type") or headers.get("content-type")

        body_text = ""
        if hasattr(resp, "text"):
            try:
                body_text = resp.text or ""
            except Exception:  # noqa: BLE001
                body_text = ""
        elif hasattr(resp, "content"):
            content = getattr(resp, "content")
            if isinstance(content, bytes):
                body_text = content.decode("utf-8", "ignore")
            else:
                body_text = str(content)
        else:
            body_text = str(resp)

        preview = body_text[:500]
        logger.error(
            "LLM HTTP 响应调试: url=%s, status=%s, content_type=%s, body_preview=%s",
            request_url or "未知",
            status_code,
            content_type,
            preview,
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送聊天请求到 LLM。

        Args:
            messages: 消息列表，例如 [{"role": "user", "content": "hello"}]
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            use_cache: 是否使用缓存（默认 True），对话场景建议设为 False
            **kwargs: 其他 LiteLLM 支持的参数

        Returns:
            LiteLLM 的响应对象（字典格式）
        """
        provider = self.config.get("provider", "openai")
        model = self.config.get("model", "gpt-4")
        params: Dict[str, Any] | None = None

        try:
            # 对于 custom provider（OpenAI 兼容的第三方 API），转换为 openai
            # 这样 LiteLLM 会使用 OpenAI 的协议格式 + 自定义 api_base
            if provider == "custom":
                provider = "openai"
                logger.info("📝 检测到 custom provider，转换为 openai 协议格式")

            # 构建完整的模型名称
            # 如果是 openai 兼容的第三方服务，通常不需要加 provider 前缀，或者直接用 model 名
            # LiteLLM 约定：对于 openai 兼容接口，如果 provider 是 openai，可以直接用 model 名
            # 如果是 anthropic/gemini 等，litellm 通常需要前缀，如 "anthropic/claude-3"
            # 这里我们做一个简单的处理：如果 provider 不是 openai，且 model 不包含 /，则加上前缀

            full_model_name = model
            if provider == "openai":
                normalized_model = model.split("/", 1)[-1]
                full_model_name = f"openai/{normalized_model}"
            elif "/" not in model:
                full_model_name = f"{provider}/{model}"
            
            # 准备参数
            params = {
                "model": full_model_name,
                "messages": messages,
                "temperature": temperature,
                "api_key": self.config["api_key"],
            }

            # GPT-5 系列模型只支持 temperature=1，必要时自动纠正
            if "gpt-5" in full_model_name.lower() and temperature != 1.0:
                logger.warning(
                    "⚠️  GPT-5 模型只支持 temperature=1，已从 %.1f 调整为 1.0",
                    temperature,
                )
                params["temperature"] = 1.0

            # 强制使用指定的 provider，防止 LiteLLM 根据模型名称自动切换
            # 例如：模型名称包含 "claude" 时，LiteLLM 会自动切换到 anthropic provider
            # 但如果用户明确指定了 openai provider（OpenAI 兼容 API），则应该尊重用户选择
            if provider == "openai":
                params["custom_llm_provider"] = "openai"

            if max_tokens:
                params["max_tokens"] = max_tokens

            # 如果有 base_url (用于 DeepSeek, Moonshot, Local 等)
            if self.config["base_url"]:
                api_base = self.config["base_url"].rstrip("/")
                if provider == "openai" and not api_base.endswith("/v1"):
                    api_base = f"{api_base}/v1"
                params["api_base"] = api_base
            
            # 如果有 api_version
            if self.config["api_version"]:
                params["api_version"] = self.config["api_version"]

            # 合并其他参数
            params.update(kwargs)

            # 添加浏览器请求头以绕过中转站 block 检测
            # 这些请求头模拟真实浏览器访问，避免被反爬虫机制拦截
            extra_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }

            # 如果有 base_url，添加 Referer 和 Origin
            if self.config["base_url"]:
                base_domain = self.config["base_url"].rstrip("/")
                extra_headers["Referer"] = f"{base_domain}/"
                extra_headers["Origin"] = base_domain

            # 合并用户自定义请求头（如果有）
            if "extra_headers" in kwargs:
                extra_headers.update(kwargs["extra_headers"])

            params["extra_headers"] = extra_headers

            logger.info(
                "📋 添加浏览器请求头: User-Agent=%s, Referer=%s",
                extra_headers.get("User-Agent", "无")[:50],
                extra_headers.get("Referer", "无"),
            )

            request_url = self._resolve_request_url(provider, params)

            cache_key = None
            if use_cache and settings.llm_cache_enabled and self.cache:
                cache_key = generate_cache_key(messages, self.config["model"], temperature)
                cached = await self.cache.get(cache_key)
                if cached:
                    logger.info("✅ LLM 缓存命中: %s", cache_key[:16])
                    return json.loads(cached)

            safe_params = params.copy()
            safe_params["api_key"] = self._mask_api_key(safe_params.get("api_key"))
            logger.info(
                "发送 LLM 请求: url=%s, params=%s",
                request_url or "未推断",
                safe_params,
            )

            # 调用 LiteLLM (异步)
            raw_response = await litellm.acompletion(**params)
            response_payload: Any | None = None
            if hasattr(raw_response, "json") and callable(getattr(raw_response, "json", None)):
                try:
                    response_payload = raw_response.json()
                except json.JSONDecodeError:
                    self._log_http_debug_response(raw_response, request_url)
                    raise
            if response_payload is not None:
                response = self._response_to_dict(response_payload)
            else:
                response = self._response_to_dict(raw_response)

            if not isinstance(response, dict):
                preview = str(response)[:500]
                logger.error(
                    "LLM 响应解析失败: url=%s, type=%s, preview=%s",
                    request_url or "未推断",
                    type(response).__name__,
                    preview,
                )
                raise ValueError("LLM 响应格式错误")

            choices = response.get("choices")
            if not isinstance(choices, list) or not choices:
                preview = json.dumps(response, ensure_ascii=False)[:500]
                logger.error(
                    "LLM 响应缺少 choices: url=%s, keys=%s, preview=%s",
                    request_url or "未推断",
                    list(response.keys()),
                    preview,
                )
                raise ValueError("LLM 响应缺少 choices")

            first_choice = choices[0]
            if not isinstance(first_choice, dict):
                preview = str(first_choice)[:300]
                logger.error(
                    "LLM choices[0] 类型异常: url=%s, type=%s, preview=%s",
                    request_url or "未推断",
                    type(first_choice).__name__,
                    preview,
                )
                raise ValueError("LLM choices[0] 类型异常")

            message = first_choice.get("message")
            if not isinstance(message, dict) or "content" not in message:
                preview = json.dumps(first_choice, ensure_ascii=False)[:500]
                logger.error(
                    "LLM 响应 message 无效: url=%s, preview=%s",
                    request_url or "未推断",
                    preview,
                )
                raise ValueError("LLM 响应缺少有效的 message.content")

            choice_count = len(choices)
            logger.info(
                "LLM 响应结构: type=%s, keys=%s, choices=%s, usage=%s",
                type(raw_response).__name__,
                list(response.keys()),
                choice_count,
                response.get("usage"),
            )

            if use_cache and settings.llm_cache_enabled and self.cache and cache_key:
                try:
                    await self.cache.set(cache_key, json.dumps(response), ttl=settings.llm_cache_ttl)
                except Exception as cache_exc:  # noqa: BLE001
                    logger.warning("写入缓存失败: %s", cache_exc)

            return response

        except LiteLLMException as api_error:
            safe_params = {}
            if params:
                safe_params = params.copy()
                safe_params["api_key"] = self._mask_api_key(safe_params.get("api_key"))
            logger.error(
                "LLM API 错误: provider=%s, model=%s, params=%s, 错误=%s",
                provider,
                model,
                safe_params,
                api_error,
                exc_info=True,
            )
            raise
        except Exception as e:  # noqa: BLE001
            logger.exception("LLM 请求失败: %s", e)
            raise

# 不再导出模块级单例实例，实例由依赖注入工厂管理
