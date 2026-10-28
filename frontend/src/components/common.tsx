import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

export function StatCard({ icon: Icon, label, value, tone = "cyan" }: { icon: LucideIcon; label: string; value: string | number; tone?: "cyan" | "emerald" | "amber" | "rose" }) {
  const toneClass = {
    cyan: "text-cyan-300 border-cyan-500/20 bg-cyan-500/5",
    emerald: "text-emerald-300 border-emerald-500/20 bg-emerald-500/5",
    amber: "text-amber-300 border-amber-500/20 bg-amber-500/5",
    rose: "text-rose-300 border-rose-500/20 bg-rose-500/5",
  }[tone];

  return (
    <div className="panel relative overflow-hidden p-5">
      <div className={`mb-4 inline-flex rounded-xl border p-2.5 ${toneClass}`}>
        <Icon size={18} />
      </div>
      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-white">{value}</p>
    </div>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  const value = severity.toLowerCase();
  const classes = value === "critical"
    ? "badge-critical"
    : value === "high"
      ? "badge-high"
      : value === "medium"
        ? "badge-medium"
        : value === "low"
          ? "badge-low"
          : "badge-info";
  return <span className={`badge ${classes}`}>{severity}</span>;
}

export function StatusBadge({ status }: { status: string }) {
  const value = status.toLowerCase();
  const classes = value === "open" || value === "active" || value === "running"
    ? "badge-ok"
    : value === "closed" || value === "completed" || value === "normal"
      ? "badge-muted"
      : "badge-warning";
  return <span className={`badge ${classes}`}>{status}</span>;
}

export function EmptyState({ title, message }: { title: string; message: string }) {
  return (
    <div className="panel flex min-h-48 flex-col items-center justify-center px-6 text-center">
      <p className="text-sm font-medium text-slate-300">{title}</p>
      <p className="mt-2 max-w-md text-xs leading-6 text-slate-500">{message}</p>
    </div>
  );
}

export function LoadingState({ label = "Loading AegisX data…" }: { label?: string }) {
  return <div className="panel flex min-h-40 items-center justify-center text-sm text-slate-500">{label}</div>;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="panel border-rose-500/20 bg-rose-500/5 p-5">
      <p className="text-sm font-medium text-rose-300">Backend connection problem</p>
      <p className="mt-2 text-xs leading-6 text-slate-400">{message}</p>
      {onRetry ? <button className="btn-secondary mt-4" onClick={onRetry}>Retry</button> : null}
    </div>
  );
}

export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <div className="mb-3 flex items-center gap-2">
          <span className="eyebrow">{eyebrow}</span>
          <span className="text-xs text-slate-600">/ AegisX</span>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">{title}</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">{description}</p>
      </div>
      {action}
    </div>
  );
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}
