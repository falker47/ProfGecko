"use client";

import { useCallback, useEffect, useState } from "react";
import { getStats } from "@/lib/admin-api";
import type { CacheStats } from "@/lib/admin-types";
import StatsCards from "./StatsCards";
import AdminActions from "./AdminActions";
import EntriesTable from "./EntriesTable";
import DebugTool from "./DebugTool";
import StopwordsManager from "./StopwordsManager";

interface AdminDashboardProps {
  secret: string;
  onAuthFailed: () => void;
}

export default function AdminDashboard({
  secret,
  onAuthFailed,
}: AdminDashboardProps) {
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchStats = useCallback(async () => {
    try {
      const data = await getStats(secret);
      setStats(data);
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      }
    }
  }, [secret, onAuthFailed]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  function handleRefresh() {
    fetchStats();
    setRefreshKey((k) => k + 1);
  }

  function handleLogout() {
    sessionStorage.removeItem("profgallade_admin_secret");
    onAuthFailed();
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-emerald-700 shadow-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <span className="text-xl">🗡️</span>
            <h1 className="text-lg font-semibold text-white">
              Pannello Admin
            </h1>
          </div>
          <button
            onClick={handleLogout}
            className="rounded-lg border border-white/30 px-3 py-1.5 text-sm text-white/90 transition-colors hover:bg-white/10"
          >
            Esci
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
        <StatsCards stats={stats} />
        <AdminActions
          secret={secret}
          onAction={handleRefresh}
          onAuthFailed={onAuthFailed}
        />
        <DebugTool secret={secret} onAuthFailed={onAuthFailed} />
        <EntriesTable
          secret={secret}
          onAuthFailed={onAuthFailed}
          refreshKey={refreshKey}
        />
        <StopwordsManager
          secret={secret}
          onChanged={handleRefresh}
          onAuthFailed={onAuthFailed}
          refreshKey={refreshKey}
        />
      </main>
    </div>
  );
}
