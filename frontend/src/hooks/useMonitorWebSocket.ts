import { useState, useEffect, useRef, useCallback } from "react";
import type {
  MonitorEvent,
  ConnectionStatus,
  MessageStats,
  WSMessage,
} from "@/types/monitor";

export interface UseMonitorWebSocketReturn {
  events: MonitorEvent[];
  connectionStatus: ConnectionStatus | null;
  stats: MessageStats | null;
  isConnected: boolean;
  clearHistory: () => void;
  resetStats: () => void;
}

const INITIAL_RECONNECT_DELAY = 1000; // 1 秒
const MAX_RECONNECT_DELAY = 30000; // 30 秒
const MAX_RECONNECT_ATTEMPTS = 10; // 最多重连 10 次
const MAX_HISTORY = 100;

export const useMonitorWebSocket = (
  url?: string,
): UseMonitorWebSocketReturn => {
  const resolvedUrl =
    url ||
    (typeof window !== "undefined"
      ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws/monitor`
      : "ws://localhost:8080/ws/monitor");
  const [events, setEvents] = useState<MonitorEvent[]>([]);
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus | null>(null);
  const [stats, setStats] = useState<MessageStats | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState<number>(0);
  const [reconnectDelay, setReconnectDelay] = useState<number>(
    INITIAL_RECONNECT_DELAY,
  );
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
  const reconnectAttemptsRef = useRef<number>(reconnectAttempts);
  const reconnectDelayRef = useRef<number>(reconnectDelay);

  useEffect(() => {
    reconnectAttemptsRef.current = reconnectAttempts;
  }, [reconnectAttempts]);

  useEffect(() => {
    reconnectDelayRef.current = reconnectDelay;
  }, [reconnectDelay]);

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    clearReconnectTimer();

    if (
      wsRef.current &&
      wsRef.current.readyState !== WebSocket.CLOSED &&
      wsRef.current.readyState !== WebSocket.CLOSING
    ) {
      return;
    }

    const ws = new WebSocket(resolvedUrl);

    ws.onopen = () => {
      console.log("[Monitor] WebSocket 已连接");
      setIsConnected(true);
      setReconnectAttempts(0);
      setReconnectDelay(INITIAL_RECONNECT_DELAY);
      reconnectAttemptsRef.current = 0;
      reconnectDelayRef.current = INITIAL_RECONNECT_DELAY;
    };

    ws.onmessage = (event) => {
      let message: WSMessage;

      try {
        message = JSON.parse(event.data) as WSMessage;
      } catch (error) {
        console.error("[Monitor] WebSocket 消息解析失败:", error);
        return;
      }

      if (message.type === "history") {
        setEvents(message.events);
      } else if (message.type === "stats") {
        setStats(message.data.stats);
        setConnectionStatus(message.data.connection_status);
      } else if (message.type === "event") {
        setEvents((prev) => [...prev, message.event].slice(-MAX_HISTORY));
      } else if (message.type === "ack") {
        console.log("[Monitor]", message.message);
      }
    };

    ws.onerror = (error) => {
      console.error("[Monitor] WebSocket 发生错误:", error);
    };

    ws.onclose = (event: CloseEvent) => {
      const isServerShutdown = event.code === 1001 || event.code === 1000;

      console.log(
        `[Monitor] WebSocket 已断开 (code: ${event.code}, reason: ${
          event.reason || "无"
        })`,
      );
      setIsConnected(false);
      setConnectionStatus(null);
      setStats(null);
      wsRef.current = null;
      clearReconnectTimer();

      const attempts = reconnectAttemptsRef.current;
      if (attempts >= MAX_RECONNECT_ATTEMPTS) {
        console.error(
          `[Monitor] 达到最大重连次数 (${MAX_RECONNECT_ATTEMPTS})，停止重连`,
        );
        return;
      }

      const delay = isServerShutdown ? 5000 : reconnectDelayRef.current;

      console.log(
        `[Monitor] 将在 ${delay / 1000} 秒后重连（第 ${attempts + 1} 次尝试）`,
      );

      reconnectTimeoutRef.current = setTimeout(() => {
        setReconnectAttempts((prev) => {
          const next = prev + 1;
          reconnectAttemptsRef.current = next;
          return next;
        });
        setReconnectDelay((prev) => {
          const next = Math.min(prev * 2, MAX_RECONNECT_DELAY);
          reconnectDelayRef.current = next;
          return next;
        });
        connect();
      }, delay);
    };

    wsRef.current = ws;
  }, [clearReconnectTimer, resolvedUrl]);

  useEffect(() => {
    connect();

    return () => {
      clearReconnectTimer();

      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect, clearReconnectTimer]);

  const clearHistory = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "clear_history" }));
      setEvents([]);
    }
  }, []);

  const resetStats = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "reset_stats" }));
    }
  }, []);

  return {
    events,
    connectionStatus,
    stats,
    isConnected,
    clearHistory,
    resetStats,
  };
};
