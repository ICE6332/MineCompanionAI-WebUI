import { createContext, useContext, useState } from "react";

export type LayoutVariant = "default" | "inset";
export type LayoutMode = "fixed" | "fluid";

interface LayoutContextValue {
  collapsible: "icon" | "off";
  variant: LayoutVariant;
  layout: LayoutMode;
  setVariant: (v: LayoutVariant) => void;
  setLayout: (m: LayoutMode) => void;
}

const LayoutContext = createContext<LayoutContextValue | null>(null);

export function LayoutProvider({ children }: { children: React.ReactNode }) {
  const [variant, setVariant] = useState<LayoutVariant>("default");
  const [layout, setLayout] = useState<LayoutMode>("fixed");

  const value: LayoutContextValue = {
    collapsible: "icon",
    variant,
    layout,
    setVariant,
    setLayout,
  };

  return (
    <LayoutContext.Provider value={value}>{children}</LayoutContext.Provider>
  );
}

export function useLayout(): LayoutContextValue {
  const ctx = useContext(LayoutContext);
  if (!ctx) {
    throw new Error("useLayout 必须在 LayoutProvider 内部使用");
  }
  return ctx;
}

