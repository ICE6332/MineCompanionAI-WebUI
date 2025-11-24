"""LLM 路由（真实服务版本）。

该路由接收玩家消息，通过 LLMService 调用真实大模型，并返回响应。
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from api.protocol import CompactProtocol
from core.dependencies import LLMDep

logger = logging.getLogger("api.routes.llm")

router = APIRouter(prefix="/api/llm", tags=["LLM"])


def _mask_api_key(api_key: Optional[str]) -> str:
    """日志中隐藏 API Key，仅展示前 8 位。"""
    if not api_key:
        return ""
    return f"{api_key[:8]}***"


class ActionCommand(BaseModel):
    """玩家指令动作。"""

    type: str = Field(..., description="动作类型")
    command: Optional[str] = Field(None, description="指令内容")


class ConversationRequest(BaseModel):
    """会话请求模型。"""

    id: Optional[str] = Field(None, description="请求唯一标识")
    type: Literal["conversation_request"] = Field(
        ..., description="消息类型，期望为 conversation_request"
    )
    playerName: str = Field(..., min_length=1, description="玩家名称")
    companionName: Optional[str] = Field(None, description="伙伴名称")
    message: Optional[str] = Field(None, description="玩家消息")
    action: Optional[List[Dict[str, Any]]] = Field(
        None, description="动作列表，保持与前端兼容"
    )
    timestamp: Optional[str] = Field(None, description="时间戳，ISO8601 字符串")
    position: Optional[Dict[str, Any]] = Field(None, description="玩家位置信息")
    health: Optional[float] = Field(None, description="玩家生命值")
    # 新增：LLM 配置
    llmConfig: Optional[Dict[str, str]] = Field(
        None, description="LLM 配置（provider, model, apiKey, baseUrl）"
    )

    model_config = ConfigDict(populate_by_name=True)


class LLMConfigRequest(BaseModel):
    """LLM 配置保存请求。"""

    provider: str = Field(..., min_length=1, description="服务提供商标识")
    model: str = Field(..., min_length=1, description="模型名称")
    apiKey: str = Field(..., description="访问密钥")
    baseUrl: str = Field(..., description="自定义 API Base URL")


@router.post("/player")
async def handle_player_request(payload: ConversationRequest, llm: LLMDep) -> Dict[str, Any]:
    """接收玩家消息，压缩为紧凑协议并调用真实 LLM 服务。"""

    standard_request: Dict[str, Any] = payload.model_dump(
        by_alias=True, exclude_none=True
    )
    masked_payload = standard_request.copy()
    llm_config_log = standard_request.get("llmConfig")
    if llm_config_log:
        masked_payload["llmConfig"] = llm_config_log.copy()
        if llm_config_log.get("apiKey"):
            masked_payload["llmConfig"]["apiKey"] = _mask_api_key(llm_config_log.get("apiKey"))
    logger.info("收到玩家 LLM 请求: payload=%s", masked_payload)

    try:
        
        # 如果前端提供了 LLM 配置，则覆盖后端默认配置
        if payload.llmConfig:
            logger.info(f"使用前端提供的 LLM 配置: provider={payload.llmConfig.get('provider')}, model={payload.llmConfig.get('model')}")
            llm.config["provider"] = payload.llmConfig.get("provider", llm.config["provider"])
            llm.config["model"] = payload.llmConfig.get("model", llm.config["model"])
            llm.config["api_key"] = payload.llmConfig.get("apiKey", llm.config["api_key"])
            llm.config["base_url"] = payload.llmConfig.get("baseUrl", llm.config["base_url"])

        api_key = llm.config.get("api_key")
        if not api_key:
            logger.error("LLM 请求失败：API Key 未配置")
            raise HTTPException(status_code=400, detail="API Key 未配置")
        
        # 1. 构造 Prompt
        player_name = standard_request.get("playerName", "Player")
        message_content = standard_request.get("message", "")
        
        # 简单的 Prompt 构造 (后续可移至 core/personality)
        messages = [
            {"role": "system", "content": f"你是一个 Minecraft 游戏中的 AI 伙伴。你的名字叫 {standard_request.get('companionName', 'AI')}。"},
            {"role": "user", "content": f"[{player_name}]: {message_content}"}
        ]

        # 2. 调用 LLM 服务（禁用缓存，确保每次对话都是新生成的）
        logger.info("LLM 消息内容: %s", messages)
        response = await llm.chat_completion(messages=messages, use_cache=False)

        # 3. 解析响应
        llm_reply = response["choices"][0]["message"]["content"]
        try:
            response_preview = json.dumps(response, ensure_ascii=False)
        except TypeError:
            response_preview = str(response)
        logger.info("LLM 原始响应（前 200 字符）: %s", response_preview[:200])
        
        # 4. 构造标准响应
        standard_response: Dict[str, Any] = {
            "type": "conversation_response",
            "playerName": player_name,
            "message": llm_reply,
            # 暂时保留简单的动作逻辑，或者让 LLM 输出 JSON 格式的动作
            "action": [], 
        }

        # 5. 协议转换 (保持兼容性)
        compact_response = CompactProtocol.compact(standard_response)
        expanded_response = CompactProtocol.parse(compact_response)
        logger.info("LLM 响应: %s", expanded_response)

        return expanded_response
    except Exception as exc:
        logger.exception("处理 LLM 请求失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"LLM 处理失败: {str(exc)}") from exc


@router.post("/config")
async def save_llm_config(payload: LLMConfigRequest, llm: LLMDep, request: Request) -> Dict[str, str]:
    """保存 LLM 配置并刷新后端依赖。"""

    settings_path = Path("config/settings.json")
    try:
        logger.info(
            "收到 LLM 配置保存请求: provider=%s, model=%s, baseUrl=%s, apiKey=%s",
            payload.provider,
            payload.model,
            payload.baseUrl,
            _mask_api_key(payload.apiKey),
        )

        config_data: Dict[str, Any] = {}
        if settings_path.exists():
            with open(settings_path, "r", encoding="utf-8") as file:
                loaded = json.load(file)
                if isinstance(loaded, dict):
                    config_data = loaded
        else:
            settings_path.parent.mkdir(parents=True, exist_ok=True)

        llm_section = config_data.get("llm", {})
        if not isinstance(llm_section, dict):
            llm_section = {}

        llm_section.update(
            {
                "provider": payload.provider,
                "model": payload.model,
                "api_key": payload.apiKey,
                "base_url": payload.baseUrl,
            }
        )
        config_data["llm"] = llm_section

        with open(settings_path, "w", encoding="utf-8") as file:
            json.dump(config_data, file, ensure_ascii=False, indent=2)

        # 热重载 HTTP 路由使用的 LLM 实例
        if hasattr(llm, "_load_config"):
            try:
                llm.config = llm._load_config()  # type: ignore[attr-defined]
                logger.info("HTTP 路由 LLM 配置已重新加载")
            except Exception as exc:  # noqa: BLE001
                logger.warning("HTTP 路由 LLM 配置热加载失败: %s", exc)

        # 热重载 WebSocket 使用的 LLM 实例
        if hasattr(request.app.state, "llm_service"):
            try:
                if hasattr(request.app.state.llm_service, "_load_config"):
                    request.app.state.llm_service.config = request.app.state.llm_service._load_config()
                    logger.info("✅ WebSocket LLM 配置已重新加载")
            except Exception as exc:  # noqa: BLE001
                logger.warning("WebSocket LLM 配置热加载失败: %s", exc)

        return {"status": "ok", "message": "配置已保存"}
    except Exception as exc:  # noqa: BLE001
        logger.exception("保存 LLM 配置失败: %s", exc)
        raise HTTPException(status_code=500, detail="保存 LLM 配置失败，请稍后重试") from exc
