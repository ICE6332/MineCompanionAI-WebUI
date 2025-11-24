import type { HTMLAttributes, PropsWithChildren } from "react";
import { useEffect, useMemo } from "react";
import { cn } from "@/lib/utils";

// 极简占位版 Carousel，提供与 inline-citation 所需的 API 兼容接口
export interface CarouselApi {
  scrollNext: () => void;
  scrollPrev: () => void;
  scrollSnapList: () => number[];
  selectedScrollSnap: () => number;
  on: (event: "select", handler: () => void) => void;
}

export interface CarouselProps extends HTMLAttributes<HTMLDivElement> {
  setApi?: (api: CarouselApi) => void;
}

export function Carousel({
  className,
  children,
  setApi,
  ...props
}: PropsWithChildren<CarouselProps>) {
  const api = useMemo<CarouselApi>(
    () => ({
      scrollNext: () => {},
      scrollPrev: () => {},
      scrollSnapList: () => [0],
      selectedScrollSnap: () => 0,
      on: (_event, _handler) => {},
    }),
    [],
  );

  useEffect(() => {
    setApi?.(api);
  }, [api, setApi]);

  return (
    <div className={cn("relative", className)} {...props}>
      {children}
    </div>
  );
}

export function CarouselContent({
  className,
  children,
  ...props
}: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div className={cn("flex", className)} {...props}>
      {children}
    </div>
  );
}

export function CarouselItem({
  className,
  children,
  ...props
}: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div className={cn("shrink-0", className)} {...props}>
      {children}
    </div>
  );
}
