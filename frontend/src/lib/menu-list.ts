import { Monitor, Settings, LayoutGrid } from "lucide-react";
import { SettingsIcon } from "@/components/ui/settings";
import { MonitorCheckIcon } from "@/components/ui/monitor-check";
import { UserRoundCheckIcon } from "@/components/ui/user-round-check";
import { BlocksIcon } from "@/components/ui/blocks";
import { BotMessageSquareIcon } from "@/components/ui/bot-message-square";

type Submenu = {
  href: string;
  label: string;
  active?: boolean;
};

type Menu = {
  href: string;
  label: string;
  active?: boolean;
  icon: any;
  submenus?: Submenu[];
};

type Group = {
  groupLabel: string;
  menus: Menu[];
};

export function getMenuList(pathname: string): Group[] {
  return [
    {
      groupLabel: "",
      menus: [
        {
          href: "/",
          label: "控制台",
          icon: BlocksIcon,
          submenus: []
        }
      ]
    },
    {
      groupLabel: "角色管理",
      menus: [
        {
          href: "/test-card",
          label: "角色测试",
          icon: UserRoundCheckIcon
        },
        {
          href: "/ai-chat",
          label: "AI 对话测试",
          icon: BotMessageSquareIcon
        }
      ]
    },
    {
      groupLabel: "系统",
      menus: [
        {
          href: "/monitor",
          label: "监控面板",
          icon: MonitorCheckIcon
        },
        {
          href: "/model-settings",
          label: "模型设置",
          icon: SettingsIcon
        }
      ]
    }
  ];
}
