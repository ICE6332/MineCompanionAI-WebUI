// 监控相关的类型定义，需与后端事件保持一致

// 事件类型枚举，用于区分不同监控事件
export type MonitorEventType =
  | 'mod_connected'
  | 'mod_disconnected'
  | 'frontend_connected'
  | 'frontend_disconnected'
  | 'message_received'
  | 'message_sent'
  | 'token_stats'
  | 'llm_request'
  | 'llm_response'
  | 'llm_error'
  | 'chat_message';

// 监控事件结构，包含基础元数据与原始载荷
export interface MonitorEvent {
  id: string;
  type: MonitorEventType;
  timestamp: string;
  data: Record<string, any>;
  severity: 'info' | 'warning' | 'error';
}

// 连接状态信息，用于前端显示模组与 LLM 状态
export interface ConnectionStatus {
  mod_client_id?: string;
  mod_connected_at?: string;
  mod_last_message_at?: string;
  llm_provider?: string;
  llm_ready: boolean;
}

// 消息统计数据，聚合消息计数与上次重置时间
export interface MessageStats {
  total_received: number;
  total_sent: number;
  messages_per_type: Record<string, number>;
  last_reset_at: string;
}

// WebSocket 历史消息，包含初始事件回放
export interface WSHistoryMessage {
  type: 'history';
  events: MonitorEvent[];
}

// WebSocket 统计消息，携带监控统计与连接状态
export interface WSStatsMessage {
  type: 'stats';
  data: {
    stats: MessageStats;
    connection_status: ConnectionStatus;
  };
}

// WebSocket 单条事件推送
export interface WSEventMessage {
  type: 'event';
  event: MonitorEvent;
}

// WebSocket 确认信息
export interface WSAckMessage {
  type: 'ack';
  message: string;
}

// WebSocket 消息联合类型，统一处理不同消息体
export type WSMessage =
  | WSHistoryMessage
  | WSStatsMessage
  | WSEventMessage
  | WSAckMessage;
