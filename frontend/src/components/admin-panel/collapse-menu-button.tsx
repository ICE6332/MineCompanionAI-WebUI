import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ChevronDown, CircleIcon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { DropdownMenuArrow } from "@radix-ui/react-dropdown-menu";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger
} from "@/components/ui/collapsible";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuSeparator
} from "@/components/ui/dropdown-menu";

type Submenu = {
  href: string;
  label: string;
  active?: boolean;
};

interface CollapseMenuButtonProps {
  icon: any;
  label: string;
  active: boolean;
  submenus: Submenu[];
  isOpen: boolean | undefined;
}

export function CollapseMenuButton({
  icon: Icon,
  label,
  active,
  submenus,
  isOpen
}: CollapseMenuButtonProps) {
  const location = useLocation();
  const pathname = location.pathname;
  const isSubmenuActive = submenus.some((submenu) =>
    submenu.active === undefined ? submenu.href === pathname : submenu.active
  );
  // 顶层激活状态：优先使用显式 active，其次根据子菜单路径匹配
  const isActive = active ?? isSubmenuActive;
  const [isCollapsed, setIsCollapsed] = useState<boolean>(isSubmenuActive);

  return isOpen ? (
    <Collapsible
      open={isCollapsed}
      onOpenChange={setIsCollapsed}
      className="w-full"
    >
      <CollapsibleTrigger
        className="[&[data-state=open]>div>div>svg]:rotate-180 mb-1"
        render={
          <Button
            variant={isActive ? "secondary" : "ghost"}
            className="w-full justify-start min-h-11 py-2"
          >
            <div className="w-full items-center flex justify-between">
              <div className="flex items-center">
                <span className="mr-4">
                  <Icon size={18} />
                </span>
                <p
                  className={cn(
                    "max-w-[150px] truncate",
                    isOpen
                      ? "translate-x-0 opacity-100"
                      : "-translate-x-96 opacity-0"
                  )}
                >
                  {label}
                </p>
              </div>
              <div
                className={cn(
                  "whitespace-nowrap",
                  isOpen
                    ? "translate-x-0 opacity-100"
                    : "-translate-x-96 opacity-0"
                )}
              >
                <HugeiconsIcon
                  icon={ChevronDown}
                  size={18}
                  className="transition-transform duration-200"
                />
              </div>
            </div>
          </Button>
        }
      />
      <CollapsibleContent className="overflow-hidden data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down">
        {submenus.map(({ href, label, active }, index) => (
          <Button
            key={index}
            variant={
              (active === undefined && pathname === href) || active
                ? "secondary"
                : "ghost"
            }
            className="w-full justify-start min-h-11 py-2 mb-1"
            render={
              <Link to={href}>
                <span className="mr-4 ml-2">
                  <HugeiconsIcon icon={CircleIcon} size={8} />
                </span>
                <p
                  className={cn(
                    "max-w-[170px] truncate",
                    isOpen
                      ? "translate-x-0 opacity-100"
                      : "-translate-x-96 opacity-0"
                  )}
                >
                  {label}
                </p>
              </Link>
            }
          />
        ))}
      </CollapsibleContent>
    </Collapsible>
  ) : (
    <DropdownMenu>
      <Tooltip delay={100}>
        <TooltipTrigger
          render={
            <DropdownMenuTrigger
              render={
                <Button
                  variant="ghost"
                  className="w-full justify-center min-h-11 py-2 mb-1"
                >
                  <div className="w-full items-center flex justify-center">
                    <div className="flex items-center">
                      <span className={cn(isOpen === false ? "" : "mr-4")}>
                        <Icon size={18} />
                      </span>
                      <p
                        className={cn(
                          "max-w-[200px] truncate",
                          isOpen === false ? "opacity-0" : "opacity-100"
                        )}
                      >
                        {label}
                      </p>
                    </div>
                  </div>
                </Button>
              }
            />
          }
        />
        <TooltipContent side="right" align="start" alignOffset={2}>
          {label}
        </TooltipContent>
      </Tooltip>
      <DropdownMenuContent side="right" sideOffset={25} align="start">
        <DropdownMenuLabel className="max-w-[190px] truncate">
          {label}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {submenus.map(({ href, label, active }, index) => (
          <DropdownMenuItem
            key={index}
            render={
              <Link
                className={`cursor-pointer ${((active === undefined && pathname === href) || active) &&
                  "bg-secondary"
                  }`}
                to={href}
              >
                <p className="max-w-[180px] truncate">{label}</p>
              </Link>
            }
          />
        ))}
        <DropdownMenuArrow className="fill-border" />
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
