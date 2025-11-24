"""监控事件类型定义。"""

from enum import Enum


class MonitorEventType(str, Enum):
    """枚举所有监控事件类型。"""

    MOD_CONNECTED: "MonitorEventType" = "mod_connected"
    MOD_DISCONNECTED: "MonitorEventType" = "mod_disconnected"
    FRONTEND_CONNECTED: "MonitorEventType" = "frontend_connected"
    FRONTEND_DISCONNECTED: "MonitorEventType" = "frontend_disconnected"
    MESSAGE_RECEIVED: "MonitorEventType" = "message_received"
    MESSAGE_SENT: "MonitorEventType" = "message_sent"
    TOKEN_STATS: "MonitorEventType" = "token_stats"
    LLM_REQUEST: "MonitorEventType" = "llm_request"
    LLM_RESPONSE: "MonitorEventType" = "llm_response"
    LLM_ERROR: "MonitorEventType" = "llm_error"
    CHAT_MESSAGE: "MonitorEventType" = "chat_message"
