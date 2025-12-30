import { Moon02Icon, Sun03Icon } from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";

export function ModeToggle() {
  const { theme, setTheme } = useTheme();

  const isDark = theme === "dark";

  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={isDark ? "切换为浅色模式" : "切换为深色模式"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      {isDark ? <HugeiconsIcon icon={Sun03Icon} className="h-4 w-4" /> : <HugeiconsIcon icon={Moon02Icon} className="h-4 w-4" />}
    </Button>
  );
}

