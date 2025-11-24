import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Activity, AlertTriangle, Clock3, Wifi, ChevronDown } from 'lucide-react';

import { ContentLayout } from '@/components/admin-panel/content-layout';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';

import type { MonitorEventType } from '@/types/monitor';

import { useMonitorWebSocket } from '@/hooks/useMonitorWebSocket';
import { useMonitorStore } from '@/stores/monitorStore';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ConnectionStatus } from './ConnectionStatus';
import { EventLog } from './EventLog';

export const MonitorPanel = () => {
  const {
    events,
    connectionStatus,
    stats,
    isConnected,
    clearHistory,
    resetStats
  } = useMonitorWebSocket();

  const {
    autoScroll,
    showTimestamps,
    toggleAutoScroll,
    toggleTimestamps,
    searchQuery,
    setSearchQuery,
    eventTypeFilter,
    setEventTypeFilter
  } = useMonitorStore();

  const eventTypeLabels: Record<MonitorEventType | 'all', string> = {
    all: '全部事件',
    mod_connected: '模组上线',
    mod_disconnected: '模组下线',
    frontend_connected: '前端连接',
    frontend_disconnected: '前端断开',
    message_received: '消息接收',
    message_sent: '消息发送',
    token_stats: 'Token 使用统计',
    llm_request: 'LLM 请求',
    llm_response: 'LLM 响应',
    llm_error: 'LLM 错误',
    chat_message: '聊天消息',
  };

  const totalMessages = useMemo(() => {
    if (!stats) return 0;
    return (stats.total_received ?? 0) + (stats.total_sent ?? 0);
  }, [stats]);

  const lastResetLabel = useMemo(() => {
    if (!stats?.last_reset_at) return '尚未重置';
    return new Date(stats.last_reset_at).toLocaleString();
  }, [stats?.last_reset_at]);

  const statCards = useMemo(
    () => [
      {
        title: '总消息数',
        value: totalMessages,
        description: `上次重置：${lastResetLabel}`,
        Icon: Activity
      },
      {
        title: 'WebSocket 状态',
        value: (
          <div className='flex items-center gap-2'>
            <span
              className={`h-2.5 w-2.5 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-slate-400'}`}
              aria-hidden
            />
            <span>{isConnected ? '已连接' : '未连接'}</span>
          </div>
        ),
        description: isConnected ? '实时同步正常' : '等待连接或检查服务器',
        Icon: Wifi
      },
      {
        title: '平均响应时间',
        value: '-- ms',
        description: '等待接入后端指标，暂作占位',
        Icon: Clock3
      },
      {
        title: '错误率',
        value: '0%',
        description: '当前未检测到错误',
        Icon: AlertTriangle
      }
    ],
    [isConnected, lastResetLabel, totalMessages]
  );

  return (
    <ContentLayout title="监控面板">
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link to="/">主页</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>监控面板</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="mt-6 space-y-6">
        {/* 标题栏 */}
        <div className="space-y-2 mb-4">
          <h2 className="text-3xl font-bold">监控面板</h2>
          <p className="text-muted-foreground">实时监控 Mod 连接和消息流</p>
        </div>

        {/* 统计卡片 */}
        <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-4'>
          {statCards.map(({ title, value, description, Icon }) => (
            <Card key={title}>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium'>{title}</CardTitle>
                <Icon className='h-5 w-5 text-muted-foreground' aria-hidden />
              </CardHeader>
              <CardContent>
                <div className='text-3xl font-bold tabular-nums'>{value}</div>
                <p className='mt-1 text-xs text-muted-foreground'>{description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* 连接状态 */}
        <ConnectionStatus isConnected={isConnected} connectionStatus={connectionStatus} />

        {/* 工具栏 */}
        <Card>
          <CardHeader className='pb-3'>
            <CardTitle className='text-base'>筛选与视图控制</CardTitle>
            <CardDescription>搜索事件、筛选类型，并切换滚动与时间戳显示</CardDescription>
          </CardHeader>
          <CardContent className='flex flex-wrap items-center gap-3 md:gap-4'>
            <div className='flex-1 min-w-[220px]'>
              <Input
                placeholder='搜索事件...'
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                className='min-h-11'
              />
            </div>
            <div className='min-w-[160px]'>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant='outline' className='w-full justify-between min-h-11'>
                    {eventTypeLabels[eventTypeFilter]}
                    <ChevronDown className='h-4 w-4 opacity-50' />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align='end' className='w-56'>
                  <DropdownMenuRadioGroup value={eventTypeFilter} onValueChange={(value) => setEventTypeFilter(value as MonitorEventType | 'all')}>
                    <DropdownMenuRadioItem value='all'>全部事件</DropdownMenuRadioItem>
                    <DropdownMenuRadioItem value='mod_connected'>模组上线</DropdownMenuRadioItem>
                    <DropdownMenuRadioItem value='mod_disconnected'>模组下线</DropdownMenuRadioItem>
                    <DropdownMenuRadioItem value='frontend_connected'>前端连接</DropdownMenuRadioItem>
                    <DropdownMenuRadioItem value='frontend_disconnected'>前端断开</DropdownMenuRadioItem>
                    <DropdownMenuRadioItem value='message_received'>消息接收</DropdownMenuRadioItem>
                    <DropdownMenuRadioItem value='message_sent'>消息发送</DropdownMenuRadioItem>
                    <DropdownMenuRadioItem value='token_stats'>Token 使用统计</DropdownMenuRadioItem>
                    <DropdownMenuRadioItem value='llm_request'>LLM 请求</DropdownMenuRadioItem>
                    <DropdownMenuRadioItem value='llm_response'>LLM 响应</DropdownMenuRadioItem>
                    <DropdownMenuRadioItem value='llm_error'>LLM 错误</DropdownMenuRadioItem>
                    <DropdownMenuRadioItem value='chat_message'>聊天消息</DropdownMenuRadioItem>
                  </DropdownMenuRadioGroup>
                </DropdownMenuContent>
              </DropdownMenu>
              </div>
              <Button
                variant={autoScroll ? 'default' : 'secondary'}
                onClick={toggleAutoScroll}
                className='min-h-11 px-4'
                aria-label='自动滚动'
              >
                {autoScroll ? '开启' : '关闭'}
              </Button>
            <Button
              variant={showTimestamps ? 'default' : 'secondary'}
              onClick={toggleTimestamps}
              className='min-h-11 px-4'
            >
              时间戳：{showTimestamps ? '显示' : '隐藏'}
            </Button>
            <Button variant='secondary' className='min-h-11 px-4' onClick={resetStats}>
              重置统计
            </Button>
            <Button variant='destructive' className='min-h-11 px-4' onClick={clearHistory}>
              清空日志
            </Button>
          </CardContent>
        </Card>

        {/* 事件日志 */}
        <div className='pt-4'>
          <EventLog events={events} />
        </div>
      </div>
    </ContentLayout>
  );
};
