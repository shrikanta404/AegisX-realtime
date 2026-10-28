import { useEffect, useState } from "react";
import { Activity, RefreshCw, Search } from "lucide-react";

import { EmptyState, ErrorState, formatDate, LoadingState, PageHeader } from "../components/common";
import { getChanges, getErrorMessage } from "../services/api";
import type { Change } from "../types/api";
import { usePolling } from "../hooks/usePolling";

export default function Changes() {
  const [changes, setChanges] = useState<Change[]>([]);
  const [domain, setDomain] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    setError("");
    getChanges({ domain: domain || undefined, limit: 200 })
      .then(setChanges)
      .catch((reason) => setError(getErrorMessage(reason)))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [domain]);

  usePolling(load, 5000, true);

  return (
    <div className="space-y-7">
      <PageHeader eyebrow="Change Intelligence" title="Change Timeline" description="Every stored difference between completed snapshots, including services, DNS records and TLS certificate metadata." action={<button className="btn-secondary" onClick={load} disabled={loading}><RefreshCw size={15} className={loading ? "animate-spin" : ""} /> Refresh</button>} />

      {loading && changes.length === 0 ? <LoadingState /> : error ? <ErrorState message={error} onRetry={load} /> : null}

      <section className="panel overflow-hidden">
        <div className="border-b border-slate-800 p-4">
          <div className="relative max-w-md">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-600" />
            <input value={domain} onChange={(event) => setDomain(event.target.value)} placeholder="Filter by authorized domain or asset…" className="field w-full pl-10" />
          </div>
        </div>

        {changes.length === 0 && !loading ? <EmptyState title="No changes recorded" message="Run two authorized inventories with a controlled lab change between them to populate the timeline." /> : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead><tr><th>Detected</th><th>Change</th><th>Asset</th><th>Previous State</th><th>Current State</th><th>Snapshot</th></tr></thead>
              <tbody>
                {changes.map((change) => (
                  <tr key={change.id}>
                    <td className="whitespace-nowrap text-xs text-slate-500">{formatDate(change.detected_at)}</td>
                    <td><div className="inline-flex items-center gap-2"><Activity size={14} className="text-cyan-400" /><span className="rounded-lg border border-slate-800 bg-slate-950 px-2 py-1 text-[11px] text-slate-300">{change.change_type}</span></div></td>
                    <td className="font-medium text-slate-200">{change.asset_identifier}</td>
                    <td className="max-w-sm"><pre className="truncate text-[11px] text-slate-600">{change.previous_state ?? "—"}</pre></td>
                    <td className="max-w-sm"><pre className="truncate text-[11px] text-slate-500">{change.current_state ?? "—"}</pre></td>
                    <td className="text-xs text-slate-600">#{change.snapshot_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
