import { useState } from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { MonitorEvent } from '@/types/monitor';

interface MessagePreviewProps {
  event: MonitorEvent;
}

export const MessagePreview = ({ event }: MessagePreviewProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const timestamp = new Date(event.timestamp).toLocaleString();
  const badgeVariant =
    event.severity === 'error'
      ? 'destructive'
      : event.severity === 'warning'
        ? 'secondary'
        : 'default';
  const toggle = () => setIsExpanded((prev) => !prev);

  return (
    <Card>
      <CardHeader>
        <div className='flex items-center justify-between'>
          <div className='flex items-center gap-2'>
            <Badge variant={badgeVariant}>{event.type}</Badge>
            <span className='text-xs text-muted-foreground'>{timestamp}</span>
          </div>
          <Button variant='link' size='sm' onClick={toggle}>
            {isExpanded ? '收起' : '展开'}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className='text-sm text-muted-foreground'>
          {isExpanded ? (
            <pre className='bg-muted p-2 rounded overflow-x-auto text-xs'>
              {JSON.stringify(event.data, null, 2)}
            </pre>
          ) : (
            <div className='truncate'>
              {JSON.stringify(event.data)}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
