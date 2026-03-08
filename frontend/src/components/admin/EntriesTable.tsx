"use client";

import { useCallback, useEffect, useState } from "react";
import { getEntries } from "@/lib/admin-api";
import type { EntriesFilters, EntriesResponse } from "@/lib/admin-types";
import EntriesFilterBar from "./EntriesFilters";
import EntryRow from "./EntryRow";
import Pagination from "./Pagination";

interface EntriesTableProps {
  secret: string;
  onAuthFailed: () => void;
  refreshKey: number;
}

const DEFAULT_FILTERS: EntriesFilters = {
  page: 1,
  per_page: 20,
  reviewed: null,
  generation: null,
  search: "",
};

export default function EntriesTable({
  secret,
  onAuthFailed,
  refreshKey,
}: EntriesTableProps) {
  const [filters, setFilters] = useState<EntriesFilters>(DEFAULT_FILTERS);
  const [data, setData] = useState<EntriesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getEntries(secret, filters);
      setData(result);
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      }
    } finally {
      setLoading(false);
    }
  }, [secret, filters, onAuthFailed]);

  useEffect(() => {
    fetchData();
  }, [fetchData, refreshKey]);

  function handlePageChange(page: number) {
    setFilters((f) => ({ ...f, page }));
    setExpandedId(null);
  }

  function handleRefetch() {
    setExpandedId(null);
    fetchData();
  }

  return (
    <div className="rounded-xl bg-white shadow-sm">
      <EntriesFilterBar filters={filters} onChange={setFilters} />

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-200 text-xs font-medium uppercase text-gray-500">
              <th className="px-3 py-2.5">ID</th>
              <th className="px-3 py-2.5">Domanda</th>
              <th className="px-3 py-2.5 text-center">Gen</th>
              <th className="px-3 py-2.5">Risposta</th>
              <th className="px-3 py-2.5 text-center">Hit</th>
              <th className="px-3 py-2.5 text-center">Rev.</th>
              <th className="px-3 py-2.5">Creata</th>
              <th className="px-3 py-2.5">Azioni</th>
            </tr>
          </thead>
          <tbody>
            {loading && !data ? (
              <tr>
                <td colSpan={8} className="py-12 text-center text-sm text-gray-400">
                  Caricamento...
                </td>
              </tr>
            ) : data && data.entries.length > 0 ? (
              data.entries.map((entry) => (
                <EntryRow
                  key={entry.id}
                  entry={entry}
                  expanded={expandedId === entry.id}
                  onToggle={() =>
                    setExpandedId(expandedId === entry.id ? null : entry.id)
                  }
                  secret={secret}
                  onUpdated={handleRefetch}
                  onAuthFailed={onAuthFailed}
                />
              ))
            ) : (
              <tr>
                <td colSpan={8} className="py-12 text-center text-sm text-gray-400">
                  Nessuna voce trovata
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {data && (
        <Pagination
          page={data.page}
          totalPages={data.total_pages}
          onChange={handlePageChange}
        />
      )}

      {data && (
        <div className="border-t border-gray-100 px-4 py-2 text-xs text-gray-400">
          {data.total} {data.total === 1 ? "voce" : "voci"} totali
        </div>
      )}
    </div>
  );
}
