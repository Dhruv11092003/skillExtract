import { cn } from "../../lib/utils";

export function Badge({ className, ...props }) {
  return (
    <span
      className={cn(
        "rounded-full border border-white/30 bg-white/10 px-3 py-1 text-xs font-medium",
        className
      )}
      {...props}
    />
  );
}
