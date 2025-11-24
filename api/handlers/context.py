"""消息处理上下文。"""

from dataclasses import dataclass
from core.interfaces import (
    EventBusInterface,
    MetricsInterface,
    LLMServiceInterface,
    ConversationContextInterface,
)


@dataclass
class HandlerContext:
    """消息处理器共享上下文。"""

    client_id: str
    event_bus: EventBusInterface
    metrics: MetricsInterface
    llm_service: LLMServiceInterface
    conversation_context: ConversationContextInterface
