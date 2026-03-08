"use client";

import type { CacheStats } from "@/lib/admin-types";

interface StatsCardsProps {
  stats: CacheStats | null;
}

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-xl bg-white p-6 shadow-sm">
      <div className="mb-2 h-4 w-24 rounded bg-gray-200" />
      <div className="h-8 w-16 rounded bg-gray-200" />
    </div>
  );
}

const CARDS = [
  { key: "total_entries", label: "Totale Voci", color: "text-emerald-600" },
  { key: "total_hits", label: "Hit Totali", color: "text-blue-600" },
  { key: "reviewed_entries", label: "Revisionate", color: "text-amber-600" },
] as const;

export default function StatsCards({ stats }: StatsCardsProps) {
  if (!stats) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {CARDS.map(({ key, label, color }) => (
        <div
          key={key}
          className="rounded-xl bg-white p-6 shadow-sm"
        >
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <p className={`mt-1 text-3xl font-bold ${color}`}>
            {stats[key].toLocaleString("it-IT")}
          </p>
        </div>
      ))}
    </div>
  );
}
