import { useEffect, useState } from "react";
import { Download, FileText, RefreshCw, Printer } from "lucide-react";

import { ErrorState, formatDate, LoadingState, PageHeader, SeverityBadge, StatCard } from "../components/common";
import { getErrorMessage, getReport } from "../services/api";
import type { SecurityReport } from "../types/api";
import { usePolling } from "../hooks/usePolling";

export default function Reports() {
  const [days, setDays] = useState(7);
  const [report, setReport] = useState<SecurityReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    setError("");
    getReport(days)
      .then(setReport)
      .catch((reason) => setError(getErrorMessage(reason)))
      .finally(() => setLoading(false));
  };

  useEffect(load, [days]);

  usePolling(load, 5000, true);

  const download = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `aegisx-security-report-${days}d.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const print = () => {
    if (!report) return;
    const lines = report.recent_findings.map((finding) => `<li><strong>${finding.title}</strong> — ${finding.asset_identifier} (${finding.severity})</li>`).join("");
    const html = `<html><head><title>AegisX Security Report</title><style>body{font-family:Inter,Arial;padding:40px;color:#0f172a}h1{margin-bottom:4px}table{border-collapse:collapse;width:100%;margin-top:20px}td,th{border:1px solid #cbd5e1;padding:8px;text-align:left}li{margin:8px 0}</style></head><body><h1>AegisX Security Report</h1><p>Generated ${formatDate(report.generated_at)} · ${days} day window</p><table><tr><th>Metric</th><th>Value</th></tr><tr><td>Snapshots</td><td>${report.summary.snapshots}</td></tr><tr><td>Changes</td><td>${report.summary.changes}</td></tr><tr><td>Findings</td><td>${report.summary.findings}</td></tr><tr><td>Open Findings</td><td>${report.summary.open_findings}</td></tr><tr><td>False Positives</td><td>${report.summary.false_positives}</td></tr><tr><td>Evidence Records</td><td>${report.summary.evidence_records}</td></tr></table><h2>Recent Findings</h2><ul>${lines || "<li>None</li>"}</ul></body></html>`;
    const popup = window.open("", "aegisx-report");
    if (!popup) return;
    popup.document.write(html);
    popup.document.close();
    popup.focus();
    popup.print();
  };

  return (
    <div className="space-y-7">
      <PageHeader eyebrow="Security Reporting" title="Reports" description="Generate a defensible monitoring summary from stored snapshots, changes, findings and evidence. Export JSON or print the current report." action={<div className="flex gap-2"><button className="btn-secondary" onClick={load} disabled={loading}><RefreshCw size={15} /> Refresh</button>{report ? <><button className="btn-secondary" onClick={download}><Download size={15} /> JSON</button><button className="btn-secondary" onClick={print}><Printer size={15} /> Print</button></> : null}</div>} />

      {loading && !report ? <LoadingState /> : error ? <ErrorState message={error} onRetry={load} /> : null}

      {report ? (
        <>
          <div className="flex flex-wrap items-center gap-2"><span className="text-xs text-slate-500">Reporting window</span>{[1, 7, 30].map((value) => <button key={value} className={`filter-chip ${days === value ? "filter-chip-active" : ""}`} onClick={() => setDays(value)}>{value} day{value > 1 ? "s" : ""}</button>)}<span className="ml-auto text-xs text-slate-600">Generated {formatDate(report.generated_at)}</span></div>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <StatCard icon={FileText} label="Snapshots" value={report.summary.snapshots} />
            <StatCard icon={FileText} label="Changes" value={report.summary.changes} tone="amber" />
            <StatCard icon={FileText} label="Findings" value={report.summary.findings} tone="rose" />
            <StatCard icon={FileText} label="Open" value={report.summary.open_findings} tone="rose" />
            <StatCard icon={FileText} label="Evidence" value={report.summary.evidence_records} tone="emerald" />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <section className="panel p-5"><h2 className="font-semibold text-white">Severity distribution</h2><div className="mt-5 space-y-3">{Object.entries(report.severity_counts).map(([key, value]) => <div key={key} className="flex items-center gap-3"><div className="w-24"><SeverityBadge severity={key} /></div><div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-800"><div className="h-full rounded-full bg-cyan-400" style={{ width: `${Math.min(value * 12, 100)}%` }} /></div><span className="w-7 text-right text-xs text-slate-500">{value}</span></div>)}</div></section>
            <section className="panel p-5"><h2 className="font-semibold text-white">Finding types</h2><div className="mt-5 space-y-3">{Object.entries(report.finding_type_counts).map(([key, value]) => <div key={key} className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-3 text-xs"><span className="text-slate-400">{key}</span><span className="font-semibold text-white">{value}</span></div>)}</div></section>
          </div>

          <section className="panel overflow-hidden"><div className="border-b border-slate-800 p-5"><h2 className="font-semibold text-white">Recent findings</h2></div>{report.recent_findings.length ? <div className="overflow-x-auto"><table className="data-table"><thead><tr><th>Finding</th><th>Severity</th><th>Asset</th><th>Status</th><th>Created</th></tr></thead><tbody>{report.recent_findings.map((finding) => <tr key={finding.id}><td className="font-medium text-slate-200">{finding.title}</td><td><SeverityBadge severity={finding.severity} /></td><td>{finding.asset_identifier}</td><td>{finding.status}</td><td>{formatDate(finding.created_at)}</td></tr>)}</tbody></table></div> : <div className="p-10 text-center text-sm text-slate-600">No findings in this reporting window.</div>}</section>
        </>
      ) : null}
    </div>
  );
}
