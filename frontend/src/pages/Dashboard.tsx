import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Globe2,
  Play,
  RefreshCw,
  Server,
  ShieldCheck,
  Wifi,
} from "lucide-react";
import { Link } from "react-router-dom";

import { ErrorState, formatDate, LoadingState, PageHeader, SeverityBadge, StatCard } from "../components/common";
import { getDashboard, getErrorMessage, getScopes, runMonitoring } from "../services/api";
import { usePolling } from "../hooks/usePolling";
import type { DashboardSummary, MonitoringResult, Scope } from "../types/api";

export default function Dashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [scopes, setScopes] = useState<Scope[]>([]);
  const [selectedDomain, setSelectedDomain] = useState("");
  const [lastLiveRun, setLastLiveRun] = useState<MonitoringResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);

  const load = async () => {
    try {
      const [dashboard, scopeData] = await Promise.all([getDashboard(), getScopes()]);
      setData(dashboard);
      setScopes(scopeData.filter((scope) => scope.is_active));
      setSelectedDomain((current) => current || scopeData.find((scope) => scope.is_active)?.domain || "");
      setError("");
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  usePolling(load, 5000, true);

  const scanNow = async () => {
    if (!selectedDomain) return;
    setScanning(true);
    setError("");
    try {
      const result = await runMonitoring(selectedDomain);
      setLastLiveRun(result);
      await load();
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Command Center"
        title="AegisX Security Operations"
        description="The dashboard is API-backed: every metric and event comes from PostgreSQL, while live collection queries only active authorized scopes."
        action={
          <button className="btn-secondary" onClick={() => void load()} disabled={loading || scanning}>
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        }
      />

      {loading && !data ? <LoadingState /> : error ? <ErrorState message={error} onRetry={() => void load()} /> : null}

      {data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <StatCard icon={Globe2} label="Authorized Scopes" value={data.scope_count} />
            <StatCard icon={Server} label="Monitored Hosts" value={data.assets.hosts} tone="emerald" />
            <StatCard icon={Activity} label="Recent Changes" value={data.recent_changes} tone="amber" />
            <StatCard icon={AlertTriangle} label="Open Findings" value={data.open_findings} tone="rose" />
            <StatCard icon={ShieldCheck} label="High / Critical" value={data.high_priority_findings} />
          </div>

          <section className="panel overflow-hidden">
            <div className="border-b border-slate-800 p-5">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Wifi size={16} className="text-cyan-300" />
                    <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-400">Live Collection</p>
                  </div>
                  <h2 className="mt-2 text-lg font-semibold text-white">Collect current website data now</h2>
                  <p className="mt-1 max-w-2xl text-xs leading-5 text-slate-500">
                    AegisX performs a fresh DNS lookup, TLS certificate observation and only the ports/checks configured in the selected authorized scope.
                  </p>
                </div>
                <div className="flex items-center gap-2 text-[11px] text-slate-500">
                  <span className={`h-2 w-2 rounded-full ${data.scheduler.running ? "bg-emerald-400" : "bg-slate-600"}`} />
                  Scheduler {data.scheduler.running ? "running" : "stopped"}
                </div>
              </div>

              <div className="mt-5 flex flex-col gap-3 lg:flex-row">
                <select className="field flex-1" value={selectedDomain} onChange={(event) => setSelectedDomain(event.target.value)}>
                  <option value="">Select an active authorized domain</option>
                  {scopes.map((scope) => (
                    <option key={scope.id} value={scope.domain}>{scope.domain}</option>
                  ))}
                </select>
                <button className="btn-primary lg:min-w-44" onClick={() => void scanNow()} disabled={scanning || !selectedDomain}>
                  <Play size={15} /> {scanning ? "Collecting live data…" : "Run live collection"}
                </button>
              </div>

              {lastLiveRun ? (
                <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
                  <div className="rounded-xl border border-emerald-500/15 bg-emerald-500/5 p-3">
                    <p className="text-[10px] uppercase tracking-widest text-emerald-300">Collected</p>
                    <p className="mt-1 text-xs text-slate-300">{lastLiveRun.domain}</p>
                    <p className="mt-1 text-[11px] text-slate-600">{formatDate(lastLiveRun.collected_at)}</p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                    <p className="text-[10px] uppercase tracking-widest text-slate-600">Resolved IP</p>
                    <p className="mt-1 text-sm text-slate-300">{lastLiveRun.live_inventory.ip_address || "Not resolved"}</p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                    <p className="text-[10px] uppercase tracking-widest text-slate-600">DNS records</p>
                    <p className="mt-1 text-lg font-semibold text-white">{lastLiveRun.live_inventory.dns_records.length}</p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                    <p className="text-[10px] uppercase tracking-widest text-slate-600">Open services</p>
                    <p className="mt-1 text-lg font-semibold text-white">{lastLiveRun.live_inventory.open_service_count}</p>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                    <p className="text-[10px] uppercase tracking-widest text-slate-600">Findings created</p>
                    <p className="mt-1 text-lg font-semibold text-white">{lastLiveRun.findings_created.length}</p>
                  </div>
                </div>
              ) : (
                <div className="mt-4 flex items-center gap-2 text-xs text-slate-600">
                  <CheckCircle2 size={14} /> No manual live collection yet. The background scheduler still monitors active scopes automatically.
                </div>
              )}
            </div>
          </section>

          <div className="grid gap-6 xl:grid-cols-[1fr_380px]">
            <section className="panel overflow-hidden">
              <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
                <div>
                  <h2 className="font-semibold text-white">Live Security Activity</h2>
                  <p className="mt-1 text-xs text-slate-500">Events generated by the current authorized monitoring data in PostgreSQL.</p>
                </div>
                <Link to="/changes" className="btn-ghost">View changes</Link>
              </div>
              <div className="divide-y divide-slate-800/70">
                {data.recent_events.length === 0 ? (
                  <div className="px-5 py-14 text-center text-sm text-slate-600">No activity recorded yet.</div>
                ) : data.recent_events.map((event) => (
                  <div key={`${event.type}-${event.id}`} className="flex items-start gap-4 px-5 py-4">
                    <div className={`mt-1 h-2 w-2 rounded-full ${event.type === "finding" ? "bg-rose-400" : "bg-cyan-400"}`} />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-sm font-medium text-slate-200">{event.title}</p>
                        {event.type === "finding" ? <SeverityBadge severity={event.severity} /> : null}
                      </div>
                      <p className="mt-1 truncate text-xs text-slate-500">{event.asset_identifier}</p>
                    </div>
                    <span className="shrink-0 text-[11px] text-slate-600">{formatDate(event.timestamp)}</span>
                  </div>
                ))}
              </div>
            </section>

            <aside className="space-y-6">
              <section className="panel p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-400">Attack Surface</p>
                    <h2 className="mt-2 text-lg font-semibold text-white">Current inventory</h2>
                  </div>
                  <ShieldCheck className="text-emerald-400" size={22} />
                </div>
                <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
                  {[
                    ["Domains", data.assets.domains],
                    ["Hosts", data.assets.hosts],
                    ["Services", data.assets.services],
                    ["DNS", data.assets.dns_records],
                    ["TLS", data.assets.tls_certificates],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
                      <p className="text-xs text-slate-600">{label}</p>
                      <p className="mt-1 text-lg font-semibold text-slate-200">{value}</p>
                    </div>
                  ))}
                </div>
              </section>

              <section className="panel p-5">
                <div className="flex items-center gap-3">
                  <Clock3 size={18} className="text-cyan-300" />
                  <div>
                    <p className="text-xs uppercase tracking-[0.16em] text-slate-600">Last completed collection</p>
                    <p className="mt-1 text-sm text-slate-300">{formatDate(data.last_scan_at)}</p>
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-2 text-xs">
                  <span className={`h-2 w-2 rounded-full ${data.scheduler.running ? "bg-emerald-400" : "bg-slate-600"}`} />
                  <span className="text-slate-500">{data.scheduler.running ? "Automatic monitoring is active" : "Automatic monitoring is stopped"}</span>
                </div>
              </section>
            </aside>
          </div>
        </>
      ) : null}
    </div>
  );
}
