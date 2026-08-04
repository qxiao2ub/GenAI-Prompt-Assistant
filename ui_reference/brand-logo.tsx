import { cn } from "@/lib/utils";

/**
 * Gen AI Prompt brand mark — a geometric "G" opening into a prompt arrow,
 * drawn as a single-weight line form so it reads at favicon size.
 */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      aria-hidden="true"
      className={cn("size-8", className)}
    >
      <path
        d="M23.5 10.2A9 9 0 1 0 25 16h-8"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M26.5 4.5v5M29 7h-5"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        opacity="0.65"
      />
    </svg>
  );
}

export function BrandLogo({
  className,
  subtitle = "Prompt assistant",
  tone = "light",
}: {
  className?: string;
  subtitle?: string | null;
  tone?: "light" | "dark";
}) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div
        className={cn(
          "flex size-10 items-center justify-center rounded-[14px] border",
          tone === "light"
            ? "border-white/15 bg-white/10 text-white"
            : "border-border bg-accent-soft text-navy",
        )}
      >
        <BrandMark className="size-[22px]" />
      </div>
      <div className="leading-tight">
        <p
          className={cn(
            "text-[15px] font-semibold tracking-[-0.01em]",
            tone === "light" ? "text-white" : "text-foreground",
          )}
        >
          Gen AI Prompt
        </p>
        {subtitle ? (
          <p
            className={cn(
              "text-[11px] tracking-wide",
              tone === "light" ? "text-white/55" : "text-muted-foreground",
            )}
          >
            {subtitle}
          </p>
        ) : null}
      </div>
    </div>
  );
}