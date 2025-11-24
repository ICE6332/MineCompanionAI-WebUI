import { useEffect, useMemo, useRef } from "react";
import type { MonitorEvent, MonitorEventType } from "@/types/monitor";
import { useMonitorStore } from "@/stores/monitorStore";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Terminal } from "@/components/ui/terminal";

const typeLabels: Record<MonitorEventType, string> = {
  mod_connected: "模组上线",
  mod_disconnected: "模组下线",
  frontend_connected: "前端连接",
  frontend_disconnected: "前端断开",
  message_received: "消息接收",
  message_sent: "消息发送",
  token_stats: "Token 使用统计",
  llm_request: "LLM 请求",
  llm_response: "LLM 响应",
  llm_error: "LLM 错误",
  chat_message: "聊天消息",
};

const severityLabels: Record<MonitorEvent["severity"], string> = {
  info: "信息",
  warning: "警告",
  error: "错误",
};

interface EventLogProps {
  events: MonitorEvent[];
}

export const EventLog = ({ events }: EventLogProps) => {
  const { showTimestamps, eventTypeFilter, searchQuery, autoScroll } =
    useMonitorStore();
  const logRef = useRef<HTMLPreElement | null>(null);

  const filteredEvents = useMemo(
    () =>
      events.filter((event) => {
        const matchesType =
          eventTypeFilter === "all" || event.type === eventTypeFilter;
        const matchesSearch =
          searchQuery === "" ||
          JSON.stringify(event)
            .toLowerCase()
            .includes(searchQuery.toLowerCase());
        return matchesType && matchesSearch;
      }),
    [events, eventTypeFilter, searchQuery],
  );

  useEffect(() => {
    if (!autoScroll || !logRef.current) return;
    // 确保新日志进来时自动滚到底部
    logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [autoScroll, filteredEvents]);

  const getColorClass = (severity: MonitorEvent["severity"]): string => {
    if (severity === "error") return "text-red-400";
    if (severity === "warning") return "text-yellow-400";
    return "text-green-400";
  };

  const logLines =
    filteredEvents.length === 0
      ? ["$ 暂无事件"]
      : filteredEvents.map((event) => {
          const payload = event.data ?? {};
          const payloadString = JSON.stringify(payload);
          const shortPayload = payloadString.substring(0, 100);
          const timeStr = showTimestamps
            ? new Date(event.timestamp).toLocaleTimeString()
            : "";

          return `[${timeStr}] ${typeLabels[event.type]} [${severityLabels[event.severity]}] ${shortPayload}${payloadString.length > 100 ? "..." : ""}`;
        });

  return (
    <Card className="max-h-[720px] flex flex-col overflow-hidden">
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="text-base font-semibold">事件日志</CardTitle>
            <CardDescription>实时事件流监控</CardDescription>
          </div>
          <div className="text-xs sm:text-sm text-muted-foreground tabular-nums whitespace-nowrap">
            已筛选 {filteredEvents.length} / 共 {events.length}
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 min-h-0 overflow-hidden">
        <Terminal contentRef={logRef}>
          {logLines.map((line, idx) => (
            <div key={idx}>{line}</div>
          ))}
        </Terminal>
      </CardContent>
    </Card>
  );
};
