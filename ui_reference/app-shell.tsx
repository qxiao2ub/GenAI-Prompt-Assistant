import { Link, useRouterState } from "@tanstack/react-router";
import {
  BookMarked,
  CircleHelp,
  GraduationCap,
  History,
  LayoutGrid,
  Menu,
  Settings,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { BrandLogo } from "@/components/brand-logo";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Workspace", icon: LayoutGrid },
  { to: "/history", label: "History", icon: History },
  { to: "/library", label: "Saved Prompts", icon: BookMarked },
  { to: "/training", label: "Training", icon: GraduationCap },
  { to: "/settings", label: "Settings", icon: Settings },
  { to: "/help", label: "Help", icon: CircleHelp },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div className="app-canvas min-h-screen">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-[264px] flex-col bg-sidebar text-sidebar-foreground transition-transform duration-300 ease-out lg:translate-x-0",
          "before:pointer-events-none before:absolute before:inset-x-0 before:top-0 before:h-64 before:bg-[radial-gradient(28rem_18rem_at_20%_0%,rgba(37,99,235,0.22),transparent_70%)]",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="relative px-5 py-6">
          <BrandLogo />
        </div>

        <nav className="relative flex-1 space-y-1 px-3">
          <p className="px-3 pt-1 pb-2 text-[10px] font-semibold tracking-[0.14em] text-white/35 uppercase">
            Workspace
          </p>
          {NAV.map(({ to, label, icon: Icon }) => {
            const active = pathname === to;
            return (
              <Link
                key={to}
                to={to}
                onClick={() => setOpen(false)}
                className={cn(
                  "group relative flex items-center gap-3 rounded-[12px] px-3 py-2.5 text-sm transition-all duration-200 ease-out",
                  active
                    ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
                    : "text-white/60 hover:bg-white/[0.06] hover:text-white",
                )}
              >
                <span
                  className={cn(
                    "absolute top-1/2 left-0 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-primary transition-opacity duration-200",
                    active ? "opacity-100" : "opacity-0",
                  )}
                />
                <Icon className="size-[18px] shrink-0" strokeWidth={1.6} />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="relative m-3 space-y-4 rounded-[16px] border border-white/10 bg-white/[0.05] p-4">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-full bg-primary/25 text-xs font-semibold text-white ring-1 ring-white/15">
              YS
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-white">Yashvi Sharma</p>
              <p className="truncate text-[11px] text-white/50">Pro workspace</p>
            </div>
            <span className="ml-auto size-1.5 rounded-full bg-success" />
          </div>
          <div>
            <div className="flex justify-between text-[11px] text-white/50">
              <span>Storage</span>
              <span className="text-white/70">1.2 / 5 GB</span>
            </div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
              <div className="h-full w-[24%] rounded-full bg-primary transition-all duration-700 ease-out" />
            </div>
          </div>
          <div className="flex items-center justify-between border-t border-white/10 pt-3">
            <span className="text-[11px] text-white/40">Version 2.4.0</span>
            <ThemeToggle className="size-8 text-white/60 hover:bg-white/10 hover:text-white" />
          </div>
        </div>
      </aside>

      {open && (
        <div
          className="fixed inset-0 z-30 bg-navy-deep/40 backdrop-blur-[2px] lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      <div className="lg:pl-[264px]">
        <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-border/70 bg-background/70 px-4 py-3 backdrop-blur-xl lg:px-10">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            aria-label="Open navigation"
            onClick={() => setOpen(true)}
          >
            <Menu className="size-5" />
          </Button>
          <p className="hidden items-center gap-2 text-sm text-muted-foreground lg:flex">
            <span className="size-1.5 rounded-full bg-primary" />
            Better prompts, better answers — every time.
          </p>
          <div className="flex items-center gap-2">
            <span className="hidden rounded-full border border-border bg-card px-3 py-1 text-[11px] font-medium text-muted-foreground sm:inline">
              Pro trial · 12 days
            </span>
            <Button size="sm">Upgrade</Button>
          </div>
        </header>
        <main className="px-4 py-8 lg:px-10">{children}</main>
      </div>
    </div>
  );
}

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle: string;
  action?: ReactNode;
}) {
  return (
    <div className="rise-in relative mb-8 overflow-hidden rounded-[22px] border border-border bg-card px-6 py-8 shadow-[var(--shadow-soft)] lg:px-9">
      <div className="hero-veil pointer-events-none absolute inset-0" />
      <div className="pointer-events-none absolute -top-16 -right-10 size-52 rounded-full bg-primary/10 blur-3xl" />
      <div className="relative flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="accent-rule mb-4" />
          <h1 className="text-3xl font-semibold tracking-[-0.02em] lg:text-[38px]">{title}</h1>
          <p className="mt-2 max-w-2xl text-[15px] text-muted-foreground">{subtitle}</p>
        </div>
        {action}
      </div>
    </div>
  );
}