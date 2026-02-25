import { cn } from "../../lib/utils";

export function Button({ className, ...props }) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold transition",
        "bg-gradient-to-r from-cyan-400 to-emerald-400 text-slate-900 hover:brightness-110",
        "disabled:opacity-60 disabled:cursor-not-allowed",
        className
      )}
      {...props}
    />
  );
}
