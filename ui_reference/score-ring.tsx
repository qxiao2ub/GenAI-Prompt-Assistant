export function scoreLabel(score: number) {
  if (score === 0) return "Awaiting prompt";
  if (score >= 85) return "Excellent";
  if (score >= 70) return "Professional";
  if (score >= 50) return "Solid start";
  return "Needs improvement";
}

export function ScoreRing({ score }: { score: number }) {
  const r = 54;
  const c = 2 * Math.PI * r;
  const offset = c - (score / 100) * c;
  return (
    <div className="relative flex items-center justify-center">
      <div className="pointer-events-none absolute size-28 rounded-full bg-primary/10 blur-2xl" />
      <svg width="140" height="140" viewBox="0 0 140 140" className="relative -rotate-90">
        <defs>
          <linearGradient id="score-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--primary)" />
            <stop offset="100%" stopColor="var(--navy)" />
          </linearGradient>
        </defs>
        <circle
          cx="70"
          cy="70"
          r={r}
          fill="none"
          strokeWidth="9"
          className="stroke-navy/10 dark:stroke-white/10"
        />
        <circle
          cx="70"
          cy="70"
          r={r}
          fill="none"
          strokeWidth="9"
          strokeLinecap="round"
          stroke="url(#score-grad)"
          className="transition-all duration-700 ease-out"
          strokeDasharray={c}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-[34px] leading-none font-semibold tracking-[-0.03em] tabular-nums">
          {score}
        </div>
        <div className="mt-1 text-[11px] tracking-wide text-muted-foreground">out of 100</div>
      </div>
    </div>
  );
}