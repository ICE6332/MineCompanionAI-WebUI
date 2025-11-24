import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

export function RecentSales() {
  return (
    <div className='space-y-8'>
      <div className='flex items-center gap-4'>
        <Avatar className='h-9 w-9'>
          <AvatarImage src='/avatars/01.png' alt='头像' />
          <AvatarFallback>AD</AvatarFallback>
        </Avatar>
        <div className='flex flex-1 flex-wrap items-center justify-between'>
          <div className='space-y-1'>
            <p className='text-sm leading-none font-medium'>伴生者 Ada</p>
            <p className='text-muted-foreground text-sm'>
              ada@companion.local
            </p>
          </div>
          <div className='font-medium'>新增 2 条对话</div>
        </div>
      </div>
      <div className='flex items-center gap-4'>
        <Avatar className='flex h-9 w-9 items-center justify-center space-y-0 border'>
          <AvatarImage src='/avatars/02.png' alt='头像' />
          <AvatarFallback>LT</AvatarFallback>
        </Avatar>
        <div className='flex flex-1 flex-wrap items-center justify-between'>
          <div className='space-y-1'>
            <p className='text-sm leading-none font-medium'>狼群塔防</p>
            <p className='text-muted-foreground text-sm'>
              系统通道 / monitor
            </p>
          </div>
          <div className='font-medium'>触发 1 次警告</div>
        </div>
      </div>
      <div className='flex items-center gap-4'>
        <Avatar className='h-9 w-9'>
          <AvatarImage src='/avatars/03.png' alt='头像' />
          <AvatarFallback>YN</AvatarFallback>
        </Avatar>
        <div className='flex flex-1 flex-wrap items-center justify-between'>
          <div className='space-y-1'>
            <p className='text-sm leading-none font-medium'>音频播报</p>
            <p className='text-muted-foreground text-sm'>
              播放「集合」提示音
            </p>
          </div>
          <div className='font-medium'>完成 3 次</div>
        </div>
      </div>

      <div className='flex items-center gap-4'>
        <Avatar className='h-9 w-9'>
          <AvatarImage src='/avatars/04.png' alt='头像' />
          <AvatarFallback>MC</AvatarFallback>
        </Avatar>
        <div className='flex flex-1 flex-wrap items-center justify-between'>
          <div className='space-y-1'>
            <p className='text-sm leading-none font-medium'>MineCompanion 核心</p>
            <p className='text-muted-foreground text-sm'>自动例行巡检</p>
          </div>
          <div className='font-medium'>完成 1 次</div>
        </div>
      </div>

      <div className='flex items-center gap-4'>
        <Avatar className='h-9 w-9'>
          <AvatarImage src='/avatars/05.png' alt='头像' />
          <AvatarFallback>QA</AvatarFallback>
        </Avatar>
        <div className='flex flex-1 flex-wrap items-center justify-between'>
          <div className='space-y-1'>
            <p className='text-sm leading-none font-medium'>QA 例行脚本</p>
            <p className='text-muted-foreground text-sm'>
              自动测试通道
            </p>
          </div>
          <div className='font-medium'>通过 12 项</div>
        </div>
      </div>
    </div>
  )
}
