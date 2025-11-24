"""LLM 路由（Mock 版本）。

该路由演示标准 JSON 请求与紧凑协议之间的转换流程，返回硬编码的对话响应。
"""

from typing import Any, Dict, List, Literal, Optional
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.protocol import CompactProtocol
from core.dependencies import LLMDep

logger = logging.getLogger("api.routes.llm")

router = APIRouter(prefix="/api/llm", tags=["LLM"])


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

    model_config = ConfigDict(populate_by_name=True)


@router.post("/player")
async def handle_player_request(payload: ConversationRequest, llm: LLMDep) -> Dict[str, Any]:
    """接收玩家消息，压缩为紧凑协议并调用真实 LLM 服务。"""

    try:
        standard_request: Dict[str, Any] = payload.model_dump(
            by_alias=True, exclude_none=True
        )
        
        # 1. 构造 Prompt
        player_name = standard_request.get("playerName", "Player")
        message_content = standard_request.get("message", "")
        
        # 简单的 Prompt 构造 (后续可移至 core/personality)
        messages = [
            {"role": "system", "content": f"你是一个 Minecraft 游戏中的 AI 伙伴。你的名字叫 {standard_request.get('companionName', 'AI')}。"},
            {"role": "user", "content": f"[{player_name}]: {message_content}"}
        ]

        # 2. 调用 LLM 服务
        logger.info(f"调用 LLM: {messages}")
        response = await llm.chat_completion(messages=messages)
        
        # 3. 解析响应
        llm_reply = response["choices"][0]["message"]["content"]
        
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
