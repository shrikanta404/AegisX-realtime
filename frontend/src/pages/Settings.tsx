import { useEffect, useState } from "react";
import { Activity, Database, Globe2, KeyRound, Play, Power, RefreshCw, ShieldCheck, Terminal } from "lucide-react";

import { ErrorState, EmptyState, formatDate, PageHeader, StatusBadge } from "../components/common";
import { createScope, deactivateScope, getAuditLogs, getErrorMessage, getScopes, getSchedulerStatus, runMonitoring, startScheduler, stopScheduler } from "../services/api";
import type { AuditLog, Scope, SchedulerStatus } from "../types/api";
import { usePolling } from "../hooks/usePolling";

export default function Settings() {
  const [scopes, setScopes] = useState<Scope[]>([]);
  const [audit, setAudit] = useState<AuditLog[]>([]);
  const [scheduler, setScheduler] = useState<SchedulerStatus | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState("");
  const [monitorResult, setMonitorResult] = useState<string>("");
  const [form, setForm] = useState({ name: "", domain: "", allowed_ports: "80,443,22,8080", allowed_checks: "dns,tls,service", description: "" });

  const load = async () => {
    setError("");
    try {
      const [scopeData, auditData, schedulerData] = await Promise.all([getScopes(), getAuditLogs(100), getSchedulerStatus()]);
      setScopes(scopeData);
      setAudit(auditData);
      setScheduler(schedulerData);
      if (!selectedDomain && scopeData[0]) setSelectedDomain(scopeData[0].domain);
    } catch (reason) {
      setError(getErrorMessage(reason));
    }
  };

  useEffect(() => { void load(); }, []);

  usePolling(load, 5000, true);

  const create = async () => {
    if (!form.name.trim() || !form.domain.trim()) return;
    setBusy(true);
    try {
      await createScope(form);
      setForm({ name: "", domain: "", allowed_ports: "80,443,22,8080", allowed_checks: "dns,tls,service", description: "" });
      await load();
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setBusy(false);
    }
  };

  const toggleScheduler = async () => {
    setBusy(true);
    try {
      const data = scheduler?.running ? await stopScheduler() : await startScheduler();
      setScheduler(data);
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setBusy(false);
    }
  };

  const runNow = async () => {
    if (!selectedDomain) return;
    setBusy(true);
    setMonitorResult("");
    try {
      const result = await runMonitoring(selectedDomain);
      setMonitorResult(`Snapshot #${result.snapshot_id} completed · ${result.change_detection.change_count ?? 0} changes · ${result.findings_created.length} findings.`);
      await load();
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setBusy(false);
    }
  };

  const deactivate = async (scope: Scope) => {
    setBusy(true);
    try {
      await deactivateScope(scope.id);
      await load();
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-7">
      <PageHeader eyebrow="System Configuration" title="Settings & Scope Control" description="Manage the authorized monitoring boundary, scheduler and operational audit trail. Secrets are never displayed by the UI." action={<button className="btn-secondary" onClick={() => void load()} disabled={busy}><RefreshCw size={15} /> Refresh</button>} />

      {error ? <ErrorState message={error} onRetry={() => void load()} /> : null}

      <div className="grid gap-6 xl:grid-cols-[1.1fr_.9fr]">
        <section className="panel p-5">
          <div className="flex items-start justify-between gap-4"><div><div className="inline-flex rounded-xl border border-cyan-500/15 bg-cyan-500/5 p-2"><ShieldCheck size={18} className="text-cyan-300" /></div><h2 className="mt-3 text-lg font-semibold text-white">Authorized scope</h2><p className="mt-1 text-xs leading-5 text-slate-500">Only active scopes can be monitored. Development controls cap the prototype at 20 active domains and 10 hosts per scope.</p></div></div>

          <div className="mt-6 space-y-3">
            {scopes.filter((scope) => scope.is_active).map((scope) => <div key={scope.id} className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-medium text-slate-200">{scope.name}</p><p className="mt-1 text-xs text-cyan-300">{scope.domain}</p></div><div className="flex items-center gap-2"><StatusBadge status="active" /><button className="btn-danger" onClick={() => void deactivate(scope)} disabled={busy}>Deactivate</button></div></div><div className="mt-3 grid gap-3 text-xs text-slate-500 sm:grid-cols-2"><span>Ports: <span className="text-slate-300">{scope.allowed_ports || "defaults"}</span></span><span>Checks: <span className="text-slate-300">{scope.allowed_checks || "defaults"}</span></span></div>{scope.description ? <p className="mt-3 text-xs leading-5 text-slate-600">{scope.description}</p> : null}</div>)}
            {scopes.filter((scope) => scope.is_active).length === 0 ? <EmptyState title="No active scopes" message="Create an explicitly authorized lab scope before running monitoring." /> : null}
          </div>

          <div className="mt-6 border-t border-slate-800 pt-6">
            <h3 className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Add authorized scope</h3>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <input className="field" placeholder="Scope name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
              <input className="field" placeholder="authorized-lab.example" value={form.domain} onChange={(event) => setForm({ ...form, domain: event.target.value })} />
              <input className="field" placeholder="80,443,8080" value={form.allowed_ports} onChange={(event) => setForm({ ...form, allowed_ports: event.target.value })} />
              <input className="field" placeholder="dns,tls,service" value={form.allowed_checks} onChange={(event) => setForm({ ...form, allowed_checks: event.target.value })} />
            </div>
            <textarea className="field mt-3 min-h-20 w-full resize-y" placeholder="Written organizer-approved scope description…" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
            <button className="btn-primary mt-3" onClick={() => void create()} disabled={busy || !form.name.trim() || !form.domain.trim()}><Globe2 size={15} /> Add scope</button>
          </div>
        </section>

        <div className="space-y-6">
          <section className="panel p-5">
            <div className="flex items-center justify-between gap-4"><div><p className="text-[10px] uppercase tracking-[0.16em] text-slate-600">Scheduled monitoring</p><h2 className="mt-2 text-lg font-semibold text-white">Scheduler control</h2></div><Activity className="text-cyan-300" size={20} /></div>
            <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-950/60 p-4"><div className="flex items-center gap-2"><span className={`h-2 w-2 rounded-full ${scheduler?.running ? "bg-emerald-400" : "bg-slate-600"}`} /><span className="text-sm text-slate-300">{scheduler?.running ? "Running" : "Stopped"}</span></div><p className="mt-2 text-xs text-slate-600">The scheduler runs the same scope-guarded monitoring pipeline as a manual run.</p><button className="btn-secondary mt-4 w-full" onClick={() => void toggleScheduler()} disabled={busy}><Power size={15} /> {scheduler?.running ? "Stop scheduler" : "Start scheduler"}</button></div>
            <div className="mt-4 flex gap-2"><select className="field flex-1" value={selectedDomain} onChange={(event) => setSelectedDomain(event.target.value)}><option value="">Select authorized domain</option>{scopes.filter((scope) => scope.is_active).map((scope) => <option key={scope.id} value={scope.domain}>{scope.domain}</option>)}</select><button className="btn-primary" onClick={() => void runNow()} disabled={busy || !selectedDomain}><Play size={15} /> Run</button></div>
            {monitorResult ? <div className="mt-3 rounded-xl border border-emerald-500/15 bg-emerald-500/5 p-3 text-xs text-emerald-300">{monitorResult}</div> : null}
          </section>

          <section className="panel p-5">
            <div className="flex items-center gap-3"><KeyRound size={18} className="text-amber-300" /><div><h2 className="font-semibold text-white">Integration status</h2><p className="mt-1 text-xs text-slate-600">API keys are handled only by the backend environment.</p></div></div>
            <div className="mt-5 grid grid-cols-2 gap-3"><div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3"><p className="text-[10px] uppercase tracking-widest text-slate-600">Gemini</p><p className="mt-2 text-xs text-slate-400">Configured via backend .env</p></div><div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3"><p className="text-[10px] uppercase tracking-widest text-slate-600">Threat Intel</p><p className="mt-2 text-xs text-slate-400">VirusTotal / AbuseIPDB</p></div></div>
          </section>
        </div>
      </div>

      <section className="panel overflow-hidden">
        <div className="flex items-center gap-3 border-b border-slate-800 p-5"><Database size={18} className="text-cyan-300" /><div><h2 className="font-semibold text-white">Audit log</h2><p className="mt-1 text-xs text-slate-600">Scope, monitoring and review actions recorded by the backend.</p></div></div>
        {audit.length === 0 ? <EmptyState title="No audit events yet" message="Operational events will appear here as scopes, scans and reviews are performed." /> : <div className="overflow-x-auto"><table className="data-table"><thead><tr><th>Time</th><th>Action</th><th>Target</th><th>Actor</th><th>Details</th></tr></thead><tbody>{audit.map((row) => <tr key={row.id}><td className="whitespace-nowrap text-xs text-slate-500">{formatDate(row.created_at)}</td><td><span className="inline-flex items-center gap-2 text-xs text-cyan-300"><Terminal size={13} /> {row.action}</span></td><td>{row.target || "—"}</td><td className="text-xs text-slate-500">{row.actor || "system"}</td><td className="max-w-xl truncate text-xs text-slate-600">{row.details || "—"}</td></tr>)}</tbody></table></div>}
      </section>
    </div>
  );
}
