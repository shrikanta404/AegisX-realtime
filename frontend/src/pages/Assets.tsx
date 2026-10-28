import { useEffect, useMemo, useState } from "react";
import { Database, Globe2, LockKeyhole, RefreshCw, Search, Server } from "lucide-react";

import { EmptyState, ErrorState, formatDate, LoadingState, PageHeader, StatCard } from "../components/common";
import { getAssets, getErrorMessage } from "../services/api";
import type { AssetItem, AssetSummary, AssetType } from "../types/api";
import { usePolling } from "../hooks/usePolling";

export default function Assets() {
  const [assets, setAssets] = useState<AssetItem[]>([]);
  const [summary, setSummary] = useState<AssetSummary | null>(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"All" | AssetType>("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    setError("");
    getAssets({ search: search || undefined })
      .then((data) => { setAssets(data.assets); setSummary(data.summary); })
      .catch((reason) => setError(getErrorMessage(reason)))
      .finally(() => setLoading(false));
  };

  usePolling(load, 5000, true);


  useEffect(() => {
    const timer = window.setTimeout(load, 180);
    return () => window.clearTimeout(timer);
    // Search should update the backend-backed list instead of filtering a fake local array.
  }, [search]);

  const filtered = useMemo(() => filter === "All" ? assets : assets.filter((item) => item.type === filter), [assets, filter]);

  return (
    <div className="space-y-7">
      <PageHeader eyebrow="Asset Intelligence" title="Asset Inventory" description="Current domains, hosts, services, DNS records and TLS certificates observed through the authorized monitoring pipeline." action={<button className="btn-secondary" onClick={load} disabled={loading}><RefreshCw size={15} className={loading ? "animate-spin" : ""} /> Refresh</button>} />

      {loading && !summary ? <LoadingState /> : error ? <ErrorState message={error} onRetry={load} /> : null}
      {summary ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          <StatCard icon={Globe2} label="Domains" value={summary.domains} />
          <StatCard icon={Server} label="Hosts" value={summary.hosts} tone="emerald" />
          <StatCard icon={Database} label="Services" value={summary.services} />
          <StatCard icon={Globe2} label="DNS Records" value={summary.dns_records} tone="amber" />
          <StatCard icon={LockKeyhole} label="TLS Certificates" value={summary.tls_certificates} tone="emerald" />
        </div>
      ) : null}

      <section className="panel overflow-hidden">
        <div className="flex flex-col gap-4 border-b border-slate-800 p-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="relative xl:max-w-md xl:flex-1">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-600" />
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search assets…" className="field w-full pl-10" />
          </div>
          <div className="flex flex-wrap gap-2">
            {(["All", "Domain", "Host", "Service", "DNS", "TLS"] as const).map((item) => (
              <button key={item} className={`filter-chip ${filter === item ? "filter-chip-active" : ""}`} onClick={() => setFilter(item)}>{item}</button>
            ))}
          </div>
        </div>

        {loading && assets.length === 0 ? <LoadingState /> : filtered.length === 0 ? <EmptyState title="No assets found" message="Run an authorized inventory to populate the current attack-surface inventory." /> : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead><tr><th>Asset</th><th>Type</th><th>Address</th><th>Status</th><th>Last Seen</th><th>Details</th></tr></thead>
              <tbody>
                {filtered.map((asset) => (
                  <tr key={asset.id}>
                    <td><p className="font-medium text-slate-200">{asset.name}</p><p className="mt-1 text-[11px] text-slate-600">scope #{asset.scope_id}</p></td>
                    <td className="text-slate-400">{asset.type}</td>
                    <td className="font-mono text-xs text-slate-400">{asset.address}</td>
                    <td><span className={`badge ${asset.status === "Warning" ? "badge-high" : asset.status === "Changed" ? "badge-medium" : "badge-ok"}`}>{asset.status}</span></td>
                    <td className="whitespace-nowrap text-xs text-slate-500">{formatDate(asset.last_seen)}</td>
                    <td className="max-w-sm text-xs leading-5 text-slate-500">{asset.details}</td>
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
