import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  Activity,
  FileText,
  Globe,
  LayoutDashboard,
  Menu,
  Search,
  Settings,
  Shield,
  TriangleAlert,
  X,
} from "lucide-react";

import { getSchedulerStatus } from "../../services/api";
import { usePolling } from "../../hooks/usePolling";

const navigation = [
  { name: "Command Center", path: "/", icon: LayoutDashboard },
  { name: "Attack Surface", path: "/attack-surface", icon: Globe },
  { name: "Assets", path: "/assets", icon: Search },
  { name: "Changes", path: "/changes", icon: Activity },
  { name: "Findings", path: "/findings", icon: TriangleAlert },
  { name: "Reports", path: "/reports", icon: FileText },
  { name: "Settings", path: "/settings", icon: Settings },
];

export default function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [schedulerRunning, setSchedulerRunning] = useState(false);

  const loadScheduler = async () => {
    try {
      const data = await getSchedulerStatus();
      setSchedulerRunning(data.running);
    } catch {
      setSchedulerRunning(false);
    }
  };

  useEffect(() => { void loadScheduler(); }, []);
  usePolling(loadScheduler, 5000, true);

  return (
    <div className="min-h-screen bg-[#020617] text-slate-100">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r border-slate-800/80 bg-slate-950/95 backdrop-blur-xl lg:block">
        <div className="flex h-20 items-center border-b border-slate-800/80 px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-cyan-500/25 bg-cyan-500/10">
              <Shield size={21} className="text-cyan-300" />
            </div>
            <div>
              <p className="text-lg font-semibold tracking-[0.2em] text-white">AEGISX</p>
              <p className="text-[10px] uppercase tracking-[0.17em] text-slate-600">Security Intelligence</p>
            </div>
          </div>
        </div>

        <div className="px-3 py-5">
          <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-600">Security Operations</p>
          <nav className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === "/"}
                  className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""}`}
                >
                  <Icon size={17} />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        <div className="absolute inset-x-3 bottom-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase tracking-[0.16em] text-slate-600">Monitor</span>
            <span className={`h-2 w-2 rounded-full ${schedulerRunning ? "bg-emerald-400 shadow-[0_0_14px_rgba(52,211,153,.7)]" : "bg-slate-600"}`} />
          </div>
          <p className="mt-2 text-xs text-slate-400">{schedulerRunning ? "Scheduled monitoring active" : "Scheduler stopped"}</p>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 border-b border-slate-800/70 bg-slate-950/85 backdrop-blur-xl">
          <div className="mx-auto flex h-16 max-w-[1700px] items-center justify-between px-5 sm:px-7">
            <div className="flex items-center gap-3">
              <button className="rounded-xl border border-slate-800 p-2 text-slate-300 lg:hidden" onClick={() => setMobileOpen((value) => !value)} aria-label="Open navigation">
                {mobileOpen ? <X size={18} /> : <Menu size={18} />}
              </button>
              <div className="hidden text-xs text-slate-500 sm:block">AUTHORIZED ATTACK-SURFACE MONITOR</div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 rounded-full border border-emerald-500/15 bg-emerald-500/5 px-3 py-1.5 text-[11px] text-emerald-300">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Scope Guard Online
              </div>
            </div>
          </div>

          {mobileOpen ? (
            <div className="border-t border-slate-800/70 bg-slate-950 px-4 py-4 lg:hidden">
              <nav className="space-y-1">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink key={item.path} to={item.path} end={item.path === "/"} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""}`}>
                      <Icon size={17} />
                      <span>{item.name}</span>
                    </NavLink>
                  );
                })}
              </nav>
            </div>
          ) : null}
        </header>

        <main className="mx-auto max-w-[1700px] px-5 py-7 sm:px-7 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
