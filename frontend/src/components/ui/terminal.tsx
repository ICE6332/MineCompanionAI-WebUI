import { cn } from "@/lib/utils";

interface TerminalProps {
  children: React.ReactNode;
  className?: string;
  contentRef?: React.Ref<HTMLPreElement>;
}

export const Terminal = ({
  children,
  className,
  contentRef,
}: TerminalProps) => {
  return (
    <div
      className={cn(
        "z-0 h-full w-full rounded-xl border border-border bg-background",
        className,
      )}
    >
      <div className="flex flex-col gap-y-2 border-b border-border p-4">
        <div className="flex flex-row gap-x-2">
          <div className="h-2 w-2 rounded-full bg-red-500"></div>
          <div className="h-2 w-2 rounded-full bg-yellow-500"></div>
          <div className="h-2 w-2 rounded-full bg-green-500"></div>
        </div>
      </div>
      <pre ref={contentRef} className="p-4 overflow-auto max-h-[520px]">
        <code className="grid gap-y-1 text-xs font-mono text-gray-900 dark:text-gray-300">
          {children}
        </code>
      </pre>
    </div>
  );
};
