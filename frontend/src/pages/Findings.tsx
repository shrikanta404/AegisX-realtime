import { useEffect, useState } from "react";
import { Bot, ChevronRight, RefreshCw, ShieldAlert, X } from "lucide-react";

import { EmptyState, ErrorState, formatDate, LoadingState, PageHeader, SeverityBadge, StatusBadge } from "../components/common";
import { analyzeFinding, getErrorMessage, getFinding, getFindings, markFalsePositive } from "../services/api";
import type { AIAnalysis, Finding, FindingDetail } from "../types/api";
import { usePolling } from "../hooks/usePolling";

export default function Findings() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [selected, setSelected] = useState<FindingDetail | null>(null);
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null);
  const [reviewReason, setReviewReason] = useState("");
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => {
    setLoading(true);
    setError("");
    getFindings({ limit: 200 })
      .then(setFindings)
      .catch((reason) => setError(getErrorMessage(reason)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  usePolling(load, 5000, true);

  const openFinding = async (id: number) => {
    setBusy(true);
    setAnalysis(null);
    try {
      setSelected(await getFinding(id));
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setBusy(false);
    }
  };

  const runAI = async () => {
    if (!selected) return;
    setBusy(true);
    try {
      setAnalysis(await analyzeFinding(selected.id));
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setBusy(false);
    }
  };

  const review = async () => {
    if (!selected || !reviewReason.trim()) return;
    setBusy(true);
    try {
      await markFalsePositive(selected.id, reviewReason.trim());
      setReviewReason("");
      const fresh = await getFinding(selected.id);
      setSelected(fresh);
      setFindings(await getFindings({ limit: 200 }));
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setBusy(false);
    }
  };

  const filtered = filter === "all" ? findings : findings.filter((item) => item.severity === filter);

  return (
    <div className="space-y-7">
      <PageHeader eyebrow="Security Findings" title="Findings & Evidence" description="Deterministic findings are tied to change or inventory evidence and can be reviewed for false positives before AI analysis." action={<button className="btn-secondary" onClick={load} disabled={loading}><RefreshCw size={15} className={loading ? "animate-spin" : ""} /> Refresh</button>} />

      {error ? <ErrorState message={error} onRetry={load} /> : null}
      {loading && findings.length === 0 ? <LoadingState /> : null}

      <div className="grid gap-6 xl:grid-cols-[1fr_420px]">
        <section className="panel overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 p-4">
            <div className="flex flex-wrap gap-2">
              {["all", "critical", "high", "medium", "low", "info"].map((value) => (
                <button key={value} className={`filter-chip ${filter === value ? "filter-chip-active" : ""}`} onClick={() => setFilter(value)}>{value}</button>
              ))}
            </div>
            <span className="text-xs text-slate-600">{filtered.length} findings</span>
          </div>
          {filtered.length === 0 ? <EmptyState title="No findings" message="Findings appear when snapshot comparisons or deterministic issue checks identify a review condition." /> : (
            <div className="divide-y divide-slate-800/70">
              {filtered.map((finding) => (
                <button key={finding.id} onClick={() => openFinding(finding.id)} className="block w-full px-5 py-4 text-left transition hover:bg-slate-900/80">
                  <div className="flex items-start gap-4">
                    <div className="mt-0.5 rounded-xl border border-rose-500/15 bg-rose-500/5 p-2"><ShieldAlert size={16} className="text-rose-300" /></div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2"><span className="text-sm font-medium text-slate-200">{finding.title}</span><SeverityBadge severity={finding.severity} /><StatusBadge status={finding.status} /></div>
                      <p className="mt-1 truncate text-xs text-slate-500">{finding.asset_identifier}</p>
                      <p className="mt-2 line-clamp-2 text-xs leading-5 text-slate-600">{finding.description}</p>
                    </div>
                    <ChevronRight size={16} className="mt-1 shrink-0 text-slate-700" />
                  </div>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="panel min-h-[540px] p-5">
          {!selected ? (
            <div className="flex h-full min-h-[500px] flex-col items-center justify-center text-center">
              <div className="rounded-2xl border border-cyan-500/15 bg-cyan-500/5 p-4"><ShieldAlert size={23} className="text-cyan-300" /></div>
              <p className="mt-4 text-sm font-medium text-slate-300">Select a finding</p>
              <p className="mt-2 max-w-xs text-xs leading-6 text-slate-600">Review evidence, mark a false positive, or ask the AI analyst to explain the supplied facts.</p>
            </div>
          ) : (
            <div>
              <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.17em] text-cyan-400">Finding #{selected.id}</p>
                  <h2 className="mt-2 text-lg font-semibold text-white">{selected.title}</h2>
                  <p className="mt-1 text-xs text-slate-500">{selected.asset_identifier}</p>
                </div>
                <button className="text-slate-600 hover:text-white" onClick={() => setSelected(null)}><X size={18} /></button>
              </div>

              <div className="mt-4 flex flex-wrap gap-2"><SeverityBadge severity={selected.severity} /><StatusBadge status={selected.status} />{selected.false_positive ? <span className="badge badge-muted">false positive</span> : null}</div>
              <p className="mt-4 text-sm leading-6 text-slate-400">{selected.description}</p>

              <div className="mt-6">
                <div className="flex items-center justify-between"><h3 className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Evidence</h3><span className="text-[11px] text-slate-700">{selected.evidence.length} records</span></div>
                <div className="mt-3 max-h-56 space-y-2 overflow-auto">
                  {selected.evidence.map((item) => (
                    <div key={item.id} className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
                      <div className="flex justify-between gap-3"><span className="text-xs font-medium text-slate-300">{item.evidence_type}</span><span className="text-[10px] text-slate-700">{formatDate(item.collected_at)}</span></div>
                      <pre className="mt-2 whitespace-pre-wrap break-words text-[10px] leading-5 text-slate-600">{item.evidence_data}</pre>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-6 border-t border-slate-800 pt-5">
                <button className="btn-primary w-full" onClick={runAI} disabled={busy}><Bot size={16} /> {busy ? "Analyzing…" : "Run AI Security Analyst"}</button>
                {analysis ? <div className="mt-3 rounded-xl border border-cyan-500/15 bg-cyan-500/5 p-4"><p className="text-[10px] uppercase tracking-[0.16em] text-cyan-400">AI Analysis · {analysis.ai_status}</p><p className="mt-2 whitespace-pre-wrap text-xs leading-6 text-slate-300">{analysis.ai_analysis}</p></div> : null}
              </div>

              {!selected.false_positive ? (
                <div className="mt-5 border-t border-slate-800 pt-5">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">False-positive review</p>
                  <textarea value={reviewReason} onChange={(event) => setReviewReason(event.target.value)} placeholder="Explain why this observation is expected…" className="field mt-3 min-h-24 w-full resize-y" />
                  <button className="btn-secondary mt-3 w-full" onClick={review} disabled={busy || reviewReason.trim().length < 3}>Mark as false positive</button>
                </div>
              ) : selected.false_positive_reason ? (
                <div className="mt-5 rounded-xl border border-amber-500/15 bg-amber-500/5 p-4"><p className="text-[10px] uppercase tracking-[0.16em] text-amber-300">Review reason</p><p className="mt-2 text-xs leading-6 text-slate-400">{selected.false_positive_reason}</p></div>
              ) : null}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
