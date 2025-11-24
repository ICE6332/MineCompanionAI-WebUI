import type { HTMLAttributes, PropsWithChildren } from "react";
import { cn } from "@/lib/utils";

export interface HoverCardProps extends HTMLAttributes<HTMLDivElement> {
  openDelay?: number;
  closeDelay?: number;
}

export function HoverCard({
  className,
  children,
  ...props
}: PropsWithChildren<HoverCardProps>) {
  return (
    <div className={cn("relative inline-block", className)} {...props}>
      {children}
    </div>
  );
}

export function HoverCardTrigger({
  className,
  children,
  ...props
}: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div className={cn("inline-flex", className)} {...props}>
      {children}
    </div>
  );
}

export function HoverCardContent({
  className,
  children,
  ...props
}: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div
      className={cn(
        "absolute left-0 top-full z-50 mt-2 rounded-md border bg-popover p-3 shadow-md",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
