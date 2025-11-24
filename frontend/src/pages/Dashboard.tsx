import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { MessageSquare, ShieldCheck, Wifi, TrendingDown } from "lucide-react";

import { ContentLayout } from "@/components/admin-panel/content-layout";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

import { Analytics } from "@/components/dashboard/analytics";
import { TokenTrendChart } from "@/components/dashboard/token-trend-chart";
import { RecentSales } from "@/components/dashboard/recent-sales";
import { useWsStore } from "@/stores/wsStore";
import { api, TokenTrendData } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import type { WsConnectionStatus } from "@/types/ws";

export function Dashboard() {
  const { status: wsStatus, messages, connect } = useWsStore();
  const [tokenTrendData, setTokenTrendData] = useState<TokenTrendData[]>([]);
  const [tokenTrendLoading, setTokenTrendLoading] = useState(true);

  useEffect(() => {
    if (wsStatus === "disconnected") {
      connect();
    }
  }, [connect, wsStatus]);

  useEffect(() => {
    const fetchTokenTrend = async () => {
      try {
        setTokenTrendLoading(true);
        const stats = await api.getTokenTrend();
        const trendData = Array.isArray(stats) ? stats : (stats as any)?.trend ?? [];
        setTokenTrendData(trendData as TokenTrendData[]);
      } catch (error) {
        console.error("Failed to fetch token trend:", error);
      } finally {
        setTokenTrendLoading(false);
      }
    };

    fetchTokenTrend();
    const interval = setInterval(fetchTokenTrend, 30000);
    return () => clearInterval(interval);
  }, []);

  const statCards = useMemo(
    () => [
      {
        label: "消息总数",
        value: messages.length,
        trend: "监控面板实时更新",
        icon: MessageSquare,
      },
      {
        label: "WebSocket 连接状态",
        value: wsStatus === "connected" ? "已连接" : wsStatus === "connecting" ? "连接中" : "未连接",
        trend: wsStatus === "connected" ? "实时同步已开启" : "等待连接或检查服务",
        icon: Wifi,
      },
      {
        label: "系统状态",
        value: wsStatus === "connected" ? "运行正常" : "待检查",
        trend: "服务自检完成",
        icon: ShieldCheck,
      },
      {
        label: "Token节省率",
        value: (() => {
          // 从 messages 过滤 token_stats 事件，兼容两种格式，取最近 10 条
          const tokenStats = messages
            .filter((msg: any) => msg.type === "token_stats" || msg.event === "token_stats")
            .slice(-10);

          if (tokenStats.length === 0) {
            return "暂无数据";
          }

          // 计算平均节省百分比
          const avgSaved =
            tokenStats.reduce((sum: number, msg: any) => {
              const percent = msg.data?.saved_percent ?? msg.saved_percent ?? 0;
              const n = Number(percent);
              return sum + (Number.isFinite(n) ? n : 0);
            }, 0) / tokenStats.length;

          return `${avgSaved.toFixed(1)}%`;
        })(),
        trend: `最近${Math.min(
          messages.filter((msg: any) => msg.type === "token_stats" || msg.event === "token_stats").length,
          10
        )}条消息统计`,
        icon: TrendingDown,
      },
    ],
    [messages.length, wsStatus, messages]
  );

  const statusTone = {
    connected: "bg-emerald-500",
    connecting: "bg-amber-500",
    disconnected: "bg-slate-400",
  } satisfies Record<WsConnectionStatus, string>;

  return (
    <ContentLayout title="控制台">
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link to="/">主页</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>控制台</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="mt-6 space-y-4">
        <div className="mb-4 flex items-center justify-between flex-wrap gap-3">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">控制台概览</h2>
            <p className="text-muted-foreground text-sm">一页掌握 Token 趋势、连接与系统健康状态</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className={`h-2.5 w-2.5 rounded-full ${statusTone[wsStatus]}`}></span>
            <span>当前连接：{wsStatus === "connected" ? "稳定" : wsStatus === "connecting" ? "建立中" : "未就绪"}</span>
          </div>
        </div>

        <Tabs orientation="vertical" defaultValue="overview" className="space-y-4">
          <div className="w-full overflow-x-auto pb-2">
            <TabsList>
              <TabsTrigger value="overview">概览</TabsTrigger>
              <TabsTrigger value="analytics">分析</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {statCards.map(({ label, value, trend, icon: Icon }) => (
                <Card key={label}>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">{label}</CardTitle>
                    <Icon className="text-muted-foreground h-4 w-4" aria-hidden="true" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold flex items-center gap-2">
                      {label === "WebSocket 连接状态" ? (
                        <Badge variant="outline" className="gap-2">
                          <span className={`h-2 w-2 rounded-full ${statusTone[wsStatus]}`}></span>
                          {value}
                        </Badge>
                      ) : label === "系统状态" ? (
                        <div className="flex items-center gap-2">
                          <span className={`h-2 w-2 rounded-full ${wsStatus === "connected" ? "bg-emerald-500" : "bg-red-500"}`}></span>
                          {value}
                        </div>
                      ) : (
                        value
                      )}
                    </div>
                    <p className="text-muted-foreground text-xs mt-1">{trend}</p>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-7">
              <TokenTrendChart
                className="col-span-1 lg:col-span-4"
                data={tokenTrendData}
                loading={tokenTrendLoading}
              />
              <Card className="col-span-1 lg:col-span-3">
                <CardHeader>
                  <CardTitle>最新活动</CardTitle>
                  <CardDescription>近期示例事件与通知</CardDescription>
                </CardHeader>
                <CardContent>
                  <RecentSales />
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-4">
            <Analytics />
          </TabsContent>
        </Tabs>
      </div>
    </ContentLayout>
  );
}
