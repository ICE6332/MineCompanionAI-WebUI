"""FastAPI 依赖注入工厂（通过 app.state 管理实例）。"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from starlette.requests import HTTPConnection

from core.interfaces import (
    EventBusInterface,
    MetricsInterface,
    LLMServiceInterface,
    ConnectionManagerInterface,
    ConversationContextInterface,
)
from core.storage.interfaces import CacheStorage

# 获取依赖实例（均由 lifespan 初始化存入 app.state）
# 使用 HTTPConnection 替代 Request，兼容 HTTP 和 WebSocket 端点


def get_event_bus(conn: HTTPConnection) -> EventBusInterface:
    return conn.app.state.event_bus


def get_metrics(conn: HTTPConnection) -> MetricsInterface:
    return conn.app.state.metrics


def get_llm_service(conn: HTTPConnection) -> LLMServiceInterface:
    return conn.app.state.llm_service


def get_connection_manager(conn: HTTPConnection) -> ConnectionManagerInterface:
    return conn.app.state.connection_manager


def get_cache_storage(conn: HTTPConnection) -> CacheStorage:
    return conn.app.state.cache_storage


def get_conversation_context(conn: HTTPConnection) -> ConversationContextInterface:
    return conn.app.state.conversation_context


# 类型别名，便于在路由上直接声明
EventBusDep = Annotated[EventBusInterface, Depends(get_event_bus)]
MetricsDep = Annotated[MetricsInterface, Depends(get_metrics)]
LLMDep = Annotated[LLMServiceInterface, Depends(get_llm_service)]
ConnectionManagerDep = Annotated[ConnectionManagerInterface, Depends(get_connection_manager)]
CacheStorageDep = Annotated[CacheStorage, Depends(get_cache_storage)]
ConversationContextDep = Annotated[ConversationContextInterface, Depends(get_conversation_context)]
