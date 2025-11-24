import { Bot, Cable, Clock3, Signal } from 'lucide-react';

import { Card, CardHeader, CardContent, CardDescription, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { ConnectionStatus as ConnectionStatusType } from '@/types/monitor';

interface ConnectionStatusProps {
  isConnected: boolean;
  connectionStatus: ConnectionStatusType | null;
}

export const ConnectionStatus = ({
  isConnected,
  connectionStatus,
}: ConnectionStatusProps) => {
  const modConnected = Boolean(isConnected && connectionStatus?.mod_client_id);
  const llmReady = Boolean(connectionStatus?.llm_ready);

  const statusDot = (active: boolean) =>
    `h-2.5 w-2.5 rounded-full ${active ? 'bg-emerald-500' : 'bg-slate-300'}`;

  return (
    <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
      <Card aria-label={`Mod 连接状态：${modConnected ? '已连接' : '未连接'}`}>
        <CardHeader className='flex flex-row items-start justify-between space-y-0 pb-3'>
          <div className='space-y-1'>
            <CardTitle className='text-base'>Mod 连接</CardTitle>
            <CardDescription>监控模组客户端在线与最近消息</CardDescription>
          </div>
          <Badge variant='outline' className='gap-2'>
            <span className={statusDot(modConnected)} aria-hidden />
            {modConnected ? '已连接' : '未连接'}
          </Badge>
        </CardHeader>
        <CardContent className='space-y-2 text-sm text-muted-foreground'>
          <div className='flex items-center gap-2'>
            <Cable className='h-4 w-4 text-muted-foreground' aria-hidden />
            <span>客户端：{connectionStatus?.mod_client_id ?? '暂无标识'}</span>
          </div>
          {connectionStatus?.mod_connected_at && (
            <div className='flex items-center gap-2'>
              <Clock3 className='h-4 w-4 text-muted-foreground' aria-hidden />
              <span>上线时间：{new Date(connectionStatus.mod_connected_at).toLocaleString()}</span>
            </div>
          )}
          {connectionStatus?.mod_last_message_at && (
            <div className='flex items-center gap-2'>
              <Signal className='h-4 w-4 text-muted-foreground' aria-hidden />
              <span>最近消息：{new Date(connectionStatus.mod_last_message_at).toLocaleString()}</span>
            </div>
          )}
          {!connectionStatus?.mod_last_message_at && (
            <div className='text-xs text-muted-foreground'>等待最新消息上报</div>
          )}
        </CardContent>
      </Card>

      <Card aria-label={`LLM 服务状态：${llmReady ? '已就绪' : '未就绪'}`}>
        <CardHeader className='flex flex-row items-start justify-between space-y-0 pb-3'>
          <div className='space-y-1'>
            <CardTitle className='text-base'>LLM 服务</CardTitle>
            <CardDescription>当前配置的模型提供商与就绪度</CardDescription>
          </div>
          <Badge variant='outline' className='gap-2'>
            <span className={statusDot(llmReady)} aria-hidden />
            {llmReady ? '已就绪' : '未就绪'}
          </Badge>
        </CardHeader>
        <CardContent className='space-y-2 text-sm text-muted-foreground'>
          <div className='flex items-center gap-2'>
            <Bot className='h-4 w-4 text-muted-foreground' aria-hidden />
            <span>服务商：{connectionStatus?.llm_provider ?? '未上报'}</span>
          </div>
          <div className='flex items-center gap-2'>
            <Signal className='h-4 w-4 text-muted-foreground' aria-hidden />
            <span>模型状态：{llmReady ? '可用' : '等待连接'}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
