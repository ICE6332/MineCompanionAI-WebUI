import { Link } from '../../router-placeholder'
import { Menu, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar'

export function AppTitle() {
  const { setOpenMobile } = useSidebar()
  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton className='gap-0 py-0 hover:bg-transparent active:bg-transparent' asChild>
          <div>
            <Link
              to='/'
              onClick={() => setOpenMobile(false)}
              className='grid flex-1 text-start text-sm leading-tight'
            >
              <span className='truncate font-bold'>Shadcn-Admin</span>
              <span className='truncate text-xs'>Vite + ShadcnUI</span>
            </Link>
            {/* 顶部模板暂未启用侧边栏按钮，保留占位 */}
          </div>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
