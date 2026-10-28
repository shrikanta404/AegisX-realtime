import { useEffect, useState } from "react";
import { Activity, Database, Globe2, RefreshCw, Server } from "lucide-react";

import AttackSurfaceScene from "../3d/AttackSurfaceScene";
import { ErrorState, LoadingState, PageHeader, StatCard } from "../components/common";
import { getAssets, getErrorMessage } from "../services/api";
import type { AssetItem, AssetSummary } from "../types/api";
import { usePolling } from "../hooks/usePolling";

export default function AttackSurface() {
  const [assets, setAssets] = useState<AssetItem[]>([]);
  const [summary, setSummary] = useState<AssetSummary | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    setError("");
    getAssets()
      .then((data) => { setAssets(data.assets); setSummary(data.summary); })
      .catch((reason) => setError(getErrorMessage(reason)))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  usePolling(load, 5000, true);

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Security Visualization"
        title="Attack Surface"
        description="A live 3D view of the assets returned by the authorized inventory service. Select nodes to inspect their current state."
        action={<button className="btn-secondary" onClick={load} disabled={loading}><RefreshCw size={15} className={loading ? "animate-spin" : ""} /> Refresh</button>}
      />

      {loading && !summary ? <LoadingState /> : error ? <ErrorState message={error} onRetry={load} /> : null}

      {summary ? (
        <>
          <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
            <StatCard icon={Globe2} label="Domains" value={summary.domains} />
            <StatCard icon={Server} label="Hosts" value={summary.hosts} tone="emerald" />
            <StatCard icon={Database} label="Services" value={summary.services} />
            <StatCard icon={Activity} label="TLS / DNS" value={`${summary.tls_certificates} / ${summary.dns_records}`} tone="amber" />
          </div>

          <div className="panel overflow-hidden">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
              <div>
                <h2 className="font-semibold text-white">Live Attack Surface Graph</h2>
                <p className="mt-1 text-xs text-slate-500">Drag to rotate · scroll to zoom · click a node for details.</p>
              </div>
              <div className="flex items-center gap-4 text-[11px] text-slate-500">
                <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-cyan-400" /> Domain</span>
                <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-sky-400" /> Host</span>
                <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-violet-400" /> Service</span>
              </div>
            </div>
            <div className="h-[620px]">
              <AttackSurfaceScene assets={assets} />
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
