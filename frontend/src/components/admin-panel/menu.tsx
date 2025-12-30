import { Ellipsis, Moon, Sun } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { useRef } from "react";

import { cn } from "@/lib/utils";
import { getMenuList } from "@/lib/menu-list";
import { Button } from "@/components/ui/button";
import { CollapseMenuButton } from "@/components/admin-panel/collapse-menu-button";
import { useTheme } from "@/components/theme-provider";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider
} from "@/components/ui/tooltip";
import type { SettingsIconHandle } from "@/components/ui/settings";
import { SunIcon } from "@/components/ui/sun";
import { MoonIcon } from "@/components/ui/moon";

interface MenuProps {
  isOpen: boolean | undefined;
}

interface MenuItemProps {
  href: string;
  label: string;
  icon: any;
  active?: boolean;
  pathname: string;
  isOpen: boolean | undefined;
}

/**
 * MenuItem 组件 - 支持动画图标的菜单项
 * 
 * 工作原理：
 * 1. 使用 useRef 创建一个指向图标的引用（iconRef）
 * 2. 将这个 ref 传递给 Icon 组件（通过 ref={iconRef}）
 * 3. 对于支持动画的图标（如 SettingsIcon），它们使用 forwardRef 暴露了控制方法：
 *    - startAnimation(): 开始动画
 *    - stopAnimation(): 停止动画
 * 4. 当鼠标悬停在整个按钮上时，通过 iconRef.current 调用这些方法
 * 5. 使用可选链操作符（?.）确保普通图标（没有这些方法）也能正常工作
 */
function MenuItem({ href, label, icon: Icon, active, pathname, isOpen }: MenuItemProps) {
  // 创建对图标组件的引用，类型为 SettingsIconHandle（定义了动画控制方法）
  const iconRef = useRef<SettingsIconHandle>(null);

  // 鼠标进入按钮时的处理函数
  const handleMouseEnter = () => {
    // 如果图标支持动画（有 startAnimation 方法），则调用它
    // 可选链 ?. 确保普通图标不会报错
    iconRef.current?.startAnimation?.();
  };

  // 鼠标离开按钮时的处理函数
  const handleMouseLeave = () => {
    // 如果图标支持动画（有 stopAnimation 方法），则调用它
    iconRef.current?.stopAnimation?.();
  };

  return (
    <div className="w-full">
      <Tooltip delay={100}>
        <TooltipTrigger render={
          <Button
            variant={
              (active === undefined && pathname.startsWith(href)) || active
                ? (isOpen === false ? "ghost" : "secondary")
                : "ghost"
            }
            className={cn(
              "w-full min-h-11 py-2 mb-1",
              isOpen === false ? "justify-center" : "justify-start"
            )}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            render={
              <Link to={href}>
                <span
                  className={cn(isOpen === false ? "" : "mr-4")}
                >
                  <Icon size={18} ref={iconRef} />
                </span>
                <p
                  className={cn(
                    "max-w-[200px] truncate",
                    isOpen === false
                      ? "hidden"
                      : "translate-x-0 opacity-100"
                  )}
                >
                  {label}
                </p>
              </Link>
            }
          />
        } />
        {isOpen === false && (
          <TooltipContent side="right">
            {label}
          </TooltipContent>
        )}
      </Tooltip>
    </div>
  );
}

export function Menu({ isOpen }: MenuProps) {
  const location = useLocation();
  const pathname = location.pathname;
  const menuList = getMenuList(pathname);
  const { resolvedTheme, toggleTheme } = useTheme();
  const isDarkMode = resolvedTheme === "dark";
  const ThemeIcon = isDarkMode ? MoonIcon : SunIcon;
  const themeLabel = isDarkMode ? "深色模式" : "浅色模式";

  const themeIconRef = useRef<SettingsIconHandle>(null);

  const handleThemeMouseEnter = () => {
    themeIconRef.current?.startAnimation?.();
  };

  const handleThemeMouseLeave = () => {
    themeIconRef.current?.stopAnimation?.();
  };

  return (
    <div className="flex-1 w-full overflow-hidden flex flex-col">
      <nav className="mt-4 h-full w-full">
        <ul className="flex flex-col h-full items-start space-y-1 px-2">
          {menuList.map(({ groupLabel, menus }, index) => (
            <li className={cn("w-full", groupLabel ? "pt-2" : "")} key={index}>
              {(isOpen && groupLabel) || isOpen === undefined ? (
                <p className="text-sm font-medium text-muted-foreground px-4 pb-2 max-w-[248px] truncate">
                  {groupLabel}
                </p>
              ) : !isOpen && isOpen !== undefined && groupLabel ? (
                <Tooltip delay={100}>
                  <TooltipTrigger className="w-full">
                    <div className="w-full flex justify-center items-center">
                      <Ellipsis className="h-5 w-5" />
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <p>{groupLabel}</p>
                  </TooltipContent>
                </Tooltip>
              ) : (
                <p className="pb-2"></p>
              )}
              {menus.map(
                ({ href, label, icon: Icon, active, submenus }, index) =>
                  !submenus || submenus.length === 0 ? (
                    <MenuItem
                      key={index}
                      href={href}
                      label={label}
                      icon={Icon}
                      active={active}
                      pathname={pathname}
                      isOpen={isOpen}
                    />
                  ) : (
                    <div className="w-full" key={index}>
                      <CollapseMenuButton
                        icon={Icon}
                        label={label}
                        active={
                          active === undefined
                            ? pathname.startsWith(href)
                            : active
                        }
                        submenus={submenus}
                        isOpen={isOpen}
                      />
                    </div>
                  )
              )}
            </li>
          ))}
          <li className="w-full grow flex flex-col justify-end gap-2">
            <Tooltip delay={100}>
              <TooltipTrigger render={
                <Button
                  onClick={toggleTheme}
                  variant="outline"
                  className="w-full justify-center min-h-11 py-2"
                  aria-label={`切换${themeLabel}`}
                  onMouseEnter={handleThemeMouseEnter}
                  onMouseLeave={handleThemeMouseLeave}
                >
                  <span className={cn(isOpen === false ? "" : "mr-4")}>
                    <ThemeIcon size={18} ref={themeIconRef} />
                  </span>
                  <p
                    className={cn(
                      "whitespace-nowrap transition-opacity duration-300",
                      isOpen === false ? "opacity-0 hidden" : "opacity-100"
                    )}
                  >
                    {themeLabel}
                  </p>
                </Button>
              } />
              {isOpen === false && (
                <TooltipContent side="right">{themeLabel}</TooltipContent>
              )}
            </Tooltip>
          </li>
        </ul>
      </nav>
    </div>
  );
}
