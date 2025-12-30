import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Message01Icon,
  Shield02Icon,
  Wifi01Icon,
  TrendingDown,
  ActivityIcon,
  ZapIcon
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";

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
import GameMessageLog from "@/components/dashboard/game-message-log";
import { useWsStore } from "@/stores/wsStore";
import { api, TokenTrendData } from "@/lib/api";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

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

  const stats = useMemo(
    () => [
      {
        title: "消息总数",
        value: messages.length.toLocaleString(),
        desc: "实时监控面板消息",
        icon: Message01Icon,
        color: "text-blue-500",
        bg: "bg-blue-500/10",
      },
      {
        title: "连接状态",
        value: wsStatus === "connected" ? "已连接" : "未连接",
        desc: wsStatus === "connected" ? "WebSocket 实时同步" : "尝试重连中...",
        icon: Wifi01Icon,
        color: wsStatus === "connected" ? "text-emerald-500" : "text-rose-500",
        bg: wsStatus === "connected" ? "bg-emerald-500/10" : "bg-rose-500/10",
        statusIndicator: true
      },
      {
        title: "系统健康",
        value: "运行正常",
        desc: "各项服务自检通过",
        icon: Shield02Icon,
        color: "text-purple-500",
        bg: "bg-purple-500/10",
      },
      {
        title: "Token 节省",
        value: (() => {
          const tokenStats = messages
            .filter((msg: any) => msg.type === "token_stats" || msg.event === "token_stats")
            .slice(-10);
          if (tokenStats.length === 0) return "N/A";
          const avg = tokenStats.reduce((sum: number, msg: any) => {
            const p = Number(msg.data?.saved_percent ?? msg.saved_percent ?? 0);
            return sum + (Number.isFinite(p) ? p : 0);
          }, 0) / tokenStats.length;
          return `${avg.toFixed(1)}%`;
        })(),
        desc: "AI 上下文优化效率",
        icon: TrendingDown,
        color: "text-orange-500",
        bg: "bg-orange-500/10",
      },
    ],
    [messages, wsStatus]
  );

  return (
    <ContentLayout title="控制台">
      <div className="w-full flex-1 flex flex-col gap-6 p-1">

        {/* Breadcrumb Header */}
        <div className="flex items-center justify-between">
          <Breadcrumb className="hidden md:flex">
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink render={<Link to="/">主页</Link>} />
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>控制台</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>

          <div className="flex items-center gap-2 text-xs font-medium px-3 py-1 rounded-full bg-accent/50 border border-border/50">
            <span className="relative flex h-2 w-2">
              <span className={cn("animate-ping absolute inline-flex h-full w-full rounded-full opacity-75", wsStatus === "connected" ? "bg-emerald-400" : "bg-red-400")}></span>
              <span className={cn("relative inline-flex rounded-full h-2 w-2", wsStatus === "connected" ? "bg-emerald-500" : "bg-red-500")}></span>
            </span>
            <span>{wsStatus === "connected" ? "系统在线" : "连接断开"}</span>
          </div>
        </div>

        {/* Main Content Tabs */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="bg-muted/50 p-1 border border-border/50">
            <TabsTrigger value="overview" className="gap-2">
              <HugeiconsIcon icon={ActivityIcon} size={16} /> 概览
            </TabsTrigger>
            <TabsTrigger value="analytics" className="gap-2">
              <HugeiconsIcon icon={ZapIcon} size={16} /> 分析
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6 animate-in fade-in-50 slide-in-from-bottom-2 duration-500">

            {/* Bento Grid Stats */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {stats.map((stat, i) => (
                <Card key={i} className="border-border/50 shadow-sm hover:shadow-md transition-all duration-300 hover:bg-accent/5 overflow-hidden relative group">
                  <div className={cn("absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity", stat.color)}>
                    <HugeiconsIcon icon={stat.icon} size={64} />
                  </div>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 z-10 relative">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      {stat.title}
                    </CardTitle>
                    <div className={cn("p-2 rounded-lg", stat.bg, stat.color)}>
                      <HugeiconsIcon icon={stat.icon} size={20} />
                    </div>
                  </CardHeader>
                  <CardContent className="z-10 relative">
                    <div className="text-2xl font-bold tracking-tight">{stat.value}</div>
                    <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                      {stat.statusIndicator && (
                        <span className={cn("h-1.5 w-1.5 rounded-full", wsStatus === "connected" ? "bg-emerald-500" : "bg-rose-500")} />
                      )}
                      {stat.desc}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Main Charts Section */}
            <div className="grid gap-4 md:grid-cols-7 lg:grid-cols-7">
              <Card className="col-span-1 md:col-span-4 shadow-sm border-border/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <HugeiconsIcon icon={TrendingDown} size={18} className="text-primary" />
                    Token 消耗趋势
                  </CardTitle>
                </CardHeader>
                <CardContent className="pl-0">
                  <TokenTrendChart data={tokenTrendData} loading={tokenTrendLoading} className="shadow-none border-0" />
                </CardContent>
              </Card>

              <Card className="col-span-1 md:col-span-3 shadow-sm border-border/50 flex flex-col">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <HugeiconsIcon icon={Message01Icon} size={18} className="text-primary" />
                    实时日志
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 min-h-[350px] p-0">
                  <GameMessageLog />
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="analytics" className="animate-in fade-in-50 slide-in-from-bottom-2 duration-500">
            <Analytics />
          </TabsContent>
        </Tabs>
      </div>
    </ContentLayout>
  );
}
