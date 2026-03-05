import { cn } from "../../lib/utils";

export function Card({ className, ...props }) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/20 bg-white/10 p-4 shadow-glass backdrop-blur-2xl",
        className
      )}
      {...props}
    />
  );
}
