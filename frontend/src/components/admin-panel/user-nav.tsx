import { Link } from "react-router-dom";
import { Layout01Icon, Logout01Icon, UserIcon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";

import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";

export function UserNav() {
  return (
    <DropdownMenu>
      <Tooltip delay={100}>
        <TooltipTrigger
          render={
            <DropdownMenuTrigger
              render={
                <Button
                  variant="outline"
                  className="relative h-8 w-8 rounded-full"
                >
                  <Avatar className="h-8 w-8">
                    <AvatarImage src="#" alt="头像" />
                    <AvatarFallback className="bg-transparent">用户</AvatarFallback>
                  </Avatar>
                </Button>
              }
            />
          }
        />
        <TooltipContent side="bottom">个人资料</TooltipContent>
      </Tooltip>

      <DropdownMenuContent className="w-56" align="end">
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">张三</p>
            <p className="text-xs leading-none text-muted-foreground">
              zhangsan@example.com
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem
            className="hover:cursor-pointer"
            render={
              <Link to="/dashboard" className="flex items-center">
                <HugeiconsIcon icon={Layout01Icon} className="w-4 h-4 mr-3 text-muted-foreground" />
                仪表盘
              </Link>
            }
          />
          <DropdownMenuItem
            className="hover:cursor-pointer"
            render={
              <Link to="/account" className="flex items-center">
                <HugeiconsIcon icon={UserIcon} className="w-4 h-4 mr-3 text-muted-foreground" />
                账户
              </Link>
            }
          />
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="hover:cursor-pointer" onClick={() => { }}>
          <HugeiconsIcon icon={Logout01Icon} className="w-4 h-4 mr-3 text-muted-foreground" />
          退出登录
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
