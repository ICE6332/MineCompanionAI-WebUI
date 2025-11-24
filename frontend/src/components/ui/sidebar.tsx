import * as React from "react";
import { cn } from "@/lib/utils";

type SidebarState = "expanded" | "collapsed";

interface SidebarContextValue {
  state: SidebarState;
  isMobile: boolean;
  setOpenMobile: (open: boolean) => void;
  toggleSidebar: () => void;
}

const SidebarContext = React.createContext<SidebarContextValue | null>(null);

export function SidebarProvider({
  children,
  defaultOpen = true,
}: {
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [state, setState] = React.useState<SidebarState>(
    defaultOpen ? "expanded" : "collapsed"
  );
  const [isMobileOpen, setIsMobileOpen] = React.useState(false);

  const isMobile = false;

  const value: SidebarContextValue = {
    state,
    isMobile,
    setOpenMobile: setIsMobileOpen,
    toggleSidebar: () =>
      setState((prev) => (prev === "expanded" ? "collapsed" : "expanded")),
  };

  return (
    <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>
  );
}

export function useSidebar(): SidebarContextValue {
  const ctx = React.useContext(SidebarContext);
  if (!ctx) {
    throw new Error("useSidebar 必须在 SidebarProvider 内部使用");
  }
  return ctx;
}

export function Sidebar({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & {
  collapsible?: "icon" | "off";
  variant?: "default" | "inset";
}) {
  return (
    <div
      data-slot="sidebar"
      className={cn("flex flex-col border-r bg-background", className)}
      {...props}
    />
  );
}

export function SidebarHeader(
  props: React.HTMLAttributes<HTMLDivElement>
) {
  return <div data-slot="sidebar-header" className="p-4" {...props} />;
}

export function SidebarContent(
  props: React.HTMLAttributes<HTMLDivElement>
) {
  return (
    <div
      data-slot="sidebar-content"
      className="flex-1 overflow-auto px-2"
      {...props}
    />
  );
}

export function SidebarFooter(
  props: React.HTMLAttributes<HTMLDivElement>
) {
  return <div data-slot="sidebar-footer" className="p-2" {...props} />;
}

export function SidebarRail(
  props: React.HTMLAttributes<HTMLDivElement>
) {
  return <div data-slot="sidebar-rail" className="w-1" {...props} />;
}

export function SidebarInset(
  props: React.HTMLAttributes<HTMLDivElement>
) {
  return <div data-slot="sidebar-inset" className="flex-1" {...props} />;
}

export function SidebarGroup(
  props: React.HTMLAttributes<HTMLDivElement>
) {
  return <div data-slot="sidebar-group" className="mb-3" {...props} />;
}

export function SidebarGroupLabel(
  props: React.HTMLAttributes<HTMLDivElement>
) {
  return (
    <div
      data-slot="sidebar-group-label"
      className="px-3 pb-1 text-xs text-muted-foreground"
      {...props}
    />
  );
}

export function SidebarMenu(
  props: React.HTMLAttributes<HTMLDivElement>
) {
  return <div data-slot="sidebar-menu" className="space-y-1" {...props} />;
}

export function SidebarMenuItem(
  props: React.LiHTMLAttributes<HTMLLIElement>
) {
  return <li data-slot="sidebar-menu-item" {...props} />;
}

export function SidebarMenuButton({
  className,
  isActive,
  tooltip,
  asChild,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  isActive?: boolean;
  tooltip?: string;
  asChild?: boolean;
}) {
  const Comp: React.ElementType = asChild ? "div" : "button";
  return (
    <Comp
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent/80",
        isActive && "bg-accent text-accent-foreground",
        className
      )}
      {...(props as any)}
    />
  );
}

export function SidebarMenuSub(
  props: React.HTMLAttributes<HTMLDivElement>
) {
  return (
    <div
      data-slot="sidebar-menu-sub"
      className="mt-1 space-y-1 pl-4"
      {...props}
    />
  );
}

export function SidebarMenuSubItem(
  props: React.LiHTMLAttributes<HTMLLIElement>
) {
  return <li data-slot="sidebar-menu-sub-item" {...props} />;
}

export function SidebarMenuSubButton({
  className,
  isActive,
  asChild,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  isActive?: boolean;
  asChild?: boolean;
}) {
  const Comp: React.ElementType = asChild ? "div" : "button";
  return (
    <Comp
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-sm hover:bg-accent/60",
        isActive && "bg-accent text-accent-foreground",
        className
      )}
      {...(props as any)}
    />
  );
}

export function SidebarTrigger({
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { toggleSidebar } = useSidebar();
  return (
    <button
      type="button"
      onClick={toggleSidebar}
      className={cn(
        "inline-flex h-8 w-8 items-center justify-center rounded-md border bg-background",
        className
      )}
      {...props}
    >
      <span className="sr-only">切换侧边栏</span>
      <div className="h-3 w-3 rounded-sm bg-foreground" />
    </button>
  );
}
