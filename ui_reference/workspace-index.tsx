import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowUpRight,
  BookOpen,
  Check,
  Copy,
  Download,
  ExternalLink,
  FileText,
  GraduationCap,
  ListChecks,
  PenLine,
  Save,
  Sparkles,
  Target,
  Users,
  Wand2,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { AppShell } from "@/components/app-shell";
import { ScoreRing, scoreLabel } from "@/components/score-ring";
import { Pill, Segmented } from "@/components/segmented";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  AUDIENCES,
  CONTEXTS,
  EXAMPLE_PROMPTS,
  FORMATS,
  LENGTHS,
  MODELS,
  TONES,
  analyze,
  improve,
  type ModelId,
  type Settings,
} from "@/lib/prompt-engine";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Gen AI Prompt — Write expert-level AI prompts" },
      {
        name: "description",
        content:
          "Turn ordinary prompts into expert-level AI instructions for ChatGPT, Claude, Gemini, Perplexity and Copilot.",
      },
      { property: "og:title", content: "Gen AI Prompt — Write expert-level AI prompts" },
      {
        property: "og:description",
        content: "An intelligent prompt assistant that scores and improves your prompts instantly.",
      },
    ],
  }),
  component: Workspace,
});

const SUPPORTED = ["ChatGPT", "Claude", "Gemini", "Perplexity", "Copilot"];

const SUGGESTION_ICONS: Record<string, typeof Sparkles> = {
  audience: Users,
  constraints: ListChecks,
  format: FileText,
  examples: BookOpen,
  broad: Target,
};

const QUICK_ACTIONS = [
  { icon: PenLine, title: "Start writing", detail: "Draft a prompt from a blank canvas." },
  { icon: Wand2, title: "Improve existing", detail: "Paste a prompt and refine it." },
  { icon: BookOpen, title: "Browse templates", detail: "Proven prompts by use case.", to: "/library" as const },
  { icon: GraduationCap, title: "Learn prompting", detail: "Short lessons on technique.", to: "/help" as const },
];

function Workspace() {
  const [prompt, setPrompt] = useState("");
  const [greeting, setGreeting] = useState("Welcome back");
  const [applied, setApplied] = useState<string[]>([]);
  const [dismissed, setDismissed] = useState<string[]>([]);
  const [settings, setSettings] = useState<Settings>({
    context: "General",
    model: "chatgpt",
    length: "Medium",
    tone: "Professional",
    audience: "Intermediate",
    format: "Bullets",
  });

  useEffect(() => {
    const h = new Date().getHours();
    setGreeting(h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening");
  }, []);

  const analysis = useMemo(() => analyze(prompt, settings), [prompt, settings]);
  const improved = useMemo(() => improve(prompt, settings, applied), [prompt, settings, applied]);
  const suggestions = analysis.suggestions.filter((s) => !dismissed.includes(s.id));

  const set = <K extends keyof Settings>(k: K, v: Settings[K]) =>
    setSettings((s) => ({ ...s, [k]: v }));

  const copy = async (text: string, label: string) => {
    await navigator.clipboard.writeText(text);
    toast.success(`${label} copied`);
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-[1400px]">
        <section className="rise-in relative mb-8 overflow-hidden rounded-[24px] border border-border bg-card px-6 py-10 shadow-[var(--shadow-soft)] lg:px-10 lg:py-12">
          <div className="hero-veil pointer-events-none absolute inset-0" />
          <div className="float-slow pointer-events-none absolute -top-20 right-4 size-56 rounded-full bg-primary/10 blur-3xl" />
          <div className="pointer-events-none absolute top-10 right-24 size-16 rotate-12 rounded-[18px] border border-primary/15" />
          <div className="pointer-events-none absolute right-10 bottom-6 size-24 rounded-full border border-navy/10" />
          <div className="pointer-events-none absolute top-16 right-56 size-2 rounded-full bg-primary/40" />

          <div className="relative max-w-3xl">
            <div className="accent-rule mb-5" />
            <p className="text-sm font-medium text-primary">{greeting}, Yashvi</p>
            <h1 className="mt-2 text-[38px] leading-[1.05] font-semibold tracking-[-0.03em] lg:text-[52px]">
              Ready to build better prompts?
            </h1>
            <p className="mt-4 max-w-xl text-[15px] leading-relaxed text-muted-foreground lg:text-base">
              Gen AI Prompt turns ordinary requests into expert-level instructions — scored, refined
              and ready for any assistant.
            </p>
            <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-muted-foreground">
              <span className="font-medium text-foreground">Supports</span>
              {SUPPORTED.map((s) => (
                <span key={s} className="flex items-center gap-1.5">
                  <Check className="size-3.5 text-success" strokeWidth={2} />
                  {s}
                </span>
              ))}
            </div>
          </div>

          <div className="relative mt-9 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {QUICK_ACTIONS.map(({ icon: Icon, title, detail, to }) => {
              const inner = (
                <>
                  <div className="flex size-9 items-center justify-center rounded-[11px] border border-border bg-accent-soft text-navy transition-colors duration-200 group-hover:bg-navy group-hover:text-navy-foreground dark:text-foreground">
                    <Icon className="size-[18px]" strokeWidth={1.6} />
                  </div>
                  <div className="mt-3.5 flex items-center gap-1.5">
                    <p className="text-sm font-medium">{title}</p>
                    <ArrowUpRight className="size-3.5 -translate-x-1 text-muted-foreground opacity-0 transition-all duration-200 group-hover:translate-x-0 group-hover:opacity-100" />
                  </div>
                  <p className="mt-1 text-[13px] text-muted-foreground">{detail}</p>
                </>
              );
              const cls =
                "press-lift card-tinted group block rounded-[16px] border border-border bg-card p-4 text-left";
              return to ? (
                <Link key={title} to={to} className={cls}>
                  {inner}
                </Link>
              ) : (
                <button
                  key={title}
                  type="button"
                  className={cls}
                  onClick={() =>
                    document
                      .getElementById("prompt-editor")
                      ?.scrollIntoView({ behavior: "smooth", block: "center" })
                  }
                >
                  {inner}
                </button>
              );
            })}
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-6">
            <div
              id="prompt-editor"
              className="card-surface group relative overflow-hidden p-6 transition-shadow duration-200 focus-within:shadow-[var(--shadow-lift),var(--shadow-glow)] lg:p-7"
            >
              <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent opacity-0 transition-opacity duration-200 group-focus-within:opacity-100" />
              <div className="mb-4 flex items-center justify-between">
                <p className="flex items-center gap-2 text-[11px] font-semibold tracking-[0.14em] text-muted-foreground uppercase">
                  <Sparkles className="size-3.5 text-primary" strokeWidth={1.8} /> Prompt editor
                </p>
                <span className="text-[11px] text-muted-foreground tabular-nums">
                  {prompt.trim() ? prompt.trim().split(/\s+/).length : 0} words
                </span>
              </div>
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="What would you like AI to help you with today?"
                className="min-h-44 resize-none border-0 bg-transparent p-0 text-lg leading-relaxed shadow-none focus-visible:ring-0"
              />
              <div className="mt-6 flex flex-wrap gap-2 border-t border-border pt-5">
                {EXAMPLE_PROMPTS.map((e) => (
                  <button
                    key={e}
                    onClick={() => setPrompt(e)}
                    className="rounded-full border border-border bg-secondary px-3.5 py-1.5 text-[13px] text-muted-foreground transition-all duration-200 ease-out hover:-translate-y-px hover:border-primary/30 hover:bg-accent-soft hover:text-accent-soft-foreground"
                  >
                    {e}
                  </button>
                ))}
              </div>
            </div>

            <div className="card-surface space-y-5 p-6">
              <div>
                <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                  Context
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {CONTEXTS.map((c) => (
                    <Pill
                      key={c}
                      active={settings.context === c}
                      onClick={() => set("context", c)}
                    >
                      {c}
                    </Pill>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                  Optimize for
                </p>
                <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {MODELS.map((m) => (
                    <button
                      key={m.id}
                      onClick={() => set("model", m.id as ModelId)}
                      className={`press-lift rounded-[14px] border p-3.5 text-left ${
                        settings.model === m.id
                          ? "border-primary/40 bg-accent-soft text-accent-soft-foreground"
                          : "border-border bg-card"
                      }`}
                    >
                      <p className="text-sm font-medium">{m.name}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{m.hint}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="card-surface space-y-5 p-6">
              <h2 className="text-base font-semibold">Prompt Settings</h2>
              <div className="grid gap-5 md:grid-cols-2">
                <Segmented
                  label="Response Length"
                  options={LENGTHS}
                  value={settings.length}
                  onChange={(v) => set("length", v)}
                />
                <Segmented
                  label="Audience"
                  options={AUDIENCES}
                  value={settings.audience}
                  onChange={(v) => set("audience", v)}
                />
                <Segmented
                  label="Tone"
                  options={TONES}
                  value={settings.tone}
                  onChange={(v) => set("tone", v)}
                />
                <Segmented
                  label="Output Format"
                  options={FORMATS}
                  value={settings.format}
                  onChange={(v) => set("format", v)}
                />
              </div>
            </div>

            {suggestions.length > 0 && prompt.trim() && (
              <div className="grid gap-3 md:grid-cols-2">
                {suggestions.map((s) => {
                  const Icon = SUGGESTION_ICONS[s.id] ?? Sparkles;
                  return (
                  <div key={s.id} className="card-surface card-tinted rise-in hover-lift p-5">
                    <div className="flex items-start gap-3">
                      <div className="flex size-9 shrink-0 items-center justify-center rounded-[11px] border border-border bg-accent-soft text-navy dark:text-foreground">
                        <Icon className="size-[18px]" strokeWidth={1.6} />
                      </div>
                      <div>
                        <p className="text-sm font-medium">{s.title}</p>
                        <p className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
                          {s.detail}
                        </p>
                      </div>
                    </div>
                    <div className="mt-4 flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => {
                          setApplied((a) => [...new Set([...a, s.fix])]);
                          setDismissed((d) => [...d, s.id]);
                          toast.success("Suggestion applied");
                        }}
                      >
                        Apply
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setDismissed((d) => [...d, s.id])}
                      >
                        Dismiss
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => toast(s.detail)}>
                        Explain
                      </Button>
                    </div>
                  </div>
                  );
                })}
              </div>
            )}

            <div className="card-surface overflow-hidden">
              <div className="grid divide-y divide-border md:grid-cols-2 md:divide-x md:divide-y-0">
                <div className="p-6">
                  <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                    Original prompt
                  </p>
                  <p className="mt-3 text-sm whitespace-pre-wrap text-muted-foreground">
                    {prompt.trim() || "Start typing to see your prompt here."}
                  </p>
                </div>
                <div className="card-tinted bg-accent-soft/50 p-6">
                  <p className="flex items-center gap-2 text-xs font-medium tracking-wide text-primary uppercase">
                    <Wand2 className="size-3.5" /> Improved prompt
                  </p>
                  <p className="mt-3 text-sm whitespace-pre-wrap">
                    {improved || "Your expert-level rewrite will appear here."}
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap gap-2 border-t border-border p-4">
                <Button size="sm" onClick={() => copy(improved, "Prompt")} disabled={!improved}>
                  <Copy className="size-4" /> Copy Prompt
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => copy("```\n" + improved + "\n```", "Markdown")}
                  disabled={!improved}
                >
                  Copy with Markdown
                </Button>
                <Button size="sm" variant="outline" disabled={!improved}>
                  <Download className="size-4" /> Export TXT
                </Button>
                <Button size="sm" variant="outline" disabled={!improved}>
                  Export PDF
                </Button>
                <Button size="sm" variant="outline" disabled={!improved}>
                  <ExternalLink className="size-4" /> Send to ChatGPT
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={!improved}
                  onClick={() => toast.success("Prompt saved to your library")}
                >
                  <Save className="size-4" /> Save
                </Button>
              </div>
            </div>
          </div>

          <aside className="space-y-6">
            <div className="card-surface card-tinted relative flex flex-col items-center overflow-hidden p-6">
              <p className="mb-5 self-start text-[11px] font-semibold tracking-[0.14em] text-muted-foreground uppercase">
                Prompt strength
              </p>
              <ScoreRing score={analysis.score} />
              <span className="mt-4 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-navy dark:text-foreground">
                {scoreLabel(analysis.score)}
              </span>
              <div className="mt-6 w-full space-y-3.5">
                {analysis.breakdown.map((b) => (
                  <div key={b.label}>
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">{b.label}</span>
                      <span className="font-medium">{b.value}</span>
                    </div>
                    <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-navy/10 dark:bg-white/10">
                      <div
                        className="h-full rounded-full bg-[image:var(--gradient-accent)] transition-all duration-700 ease-out"
                        style={{ width: `${b.value}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card-surface p-6">
              <h2 className="flex items-center gap-2 text-sm font-semibold">
                <span className="size-1.5 rounded-full bg-primary" /> Today's Activity
              </h2>
              <dl className="mt-4 space-y-3 text-sm">
                {[
                  ["Prompts improved", "14"],
                  ["Average quality score", "86"],
                  ["Time saved", "1h 20m"],
                  ["Favorite category", "Business"],
                  ["Most used AI", "ChatGPT"],
                  ["Weekly improvement", "+12%"],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <dt className="text-muted-foreground">{k}</dt>
                    <dd className="font-medium">{v}</dd>
                  </div>
                ))}
              </dl>
            </div>

            <div className="card-surface p-6">
              <h2 className="flex items-center gap-2 text-sm font-semibold">
                <span className="size-1.5 rounded-full bg-success" /> Recent Improvements
              </h2>
              <ul className="mt-4 space-y-3 text-sm">
                {[
                  ["Quarterly update email", "+31"],
                  ["Market research brief", "+24"],
                  ["Lesson plan outline", "+18"],
                ].map(([t, d]) => (
                  <li key={t} className="flex items-center justify-between gap-3">
                    <span className="truncate text-muted-foreground">{t}</span>
                    <span className="rounded-full bg-success/15 px-2 py-0.5 text-xs font-medium text-success">
                      {d}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
