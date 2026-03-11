"use client";

import { useCallback, useEffect, useState } from "react";
import { getEntries } from "@/lib/admin-api";
import type {
  EntriesFilters,
  EntriesResponse,
  SortColumn,
  SortOrder,
} from "@/lib/admin-types";
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
  feedback: null,
  sort_by: "id",
  sort_order: "desc",
};

/* ── Sortable column header ─────────────────────────────────────── */

interface SortableThProps {
  label: string;
  column: SortColumn;
  currentSort: SortColumn;
  currentOrder: SortOrder;
  onSort: (col: SortColumn) => void;
  className?: string;
}

function SortableTh({
  label,
  column,
  currentSort,
  currentOrder,
  onSort,
  className = "",
}: SortableThProps) {
  const isActive = currentSort === column;
  return (
    <th
      className={`px-3 py-2.5 select-none cursor-pointer hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors ${className}`}
      onClick={() => onSort(column)}
      title={`Ordina per ${label}`}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        <span className={`text-[10px] ${isActive ? "text-emerald-600 dark:text-emerald-400" : "text-gray-300 dark:text-gray-600"}`}>
          {isActive ? (currentOrder === "asc" ? "\u25B2" : "\u25BC") : "\u25B4\u25BE"}
        </span>
      </span>
    </th>
  );
}

/* ── Main table ─────────────────────────────────────────────────── */

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

  function handleSort(column: SortColumn) {
    setFilters((f) => {
      const sameColumn = f.sort_by === column;
      return {
        ...f,
        page: 1,
        sort_by: column,
        sort_order: sameColumn ? (f.sort_order === "asc" ? "desc" : "asc") : "desc",
      };
    });
    setExpandedId(null);
  }

  return (
    <div className="rounded-xl bg-white dark:bg-gray-900 shadow-sm">
      <EntriesFilterBar filters={filters} onChange={setFilters} />

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700 text-xs font-medium uppercase text-gray-500 dark:text-gray-400">
              <SortableTh
                label="ID"
                column="id"
                currentSort={filters.sort_by}
                currentOrder={filters.sort_order}
                onSort={handleSort}
              />
              <th className="px-3 py-2.5">Domanda</th>
              <SortableTh
                label="Gen"
                column="generation"
                currentSort={filters.sort_by}
                currentOrder={filters.sort_order}
                onSort={handleSort}
                className="text-center"
              />
              <th className="px-3 py-2.5">Risposta</th>
              <SortableTh
                label="Hit"
                column="hit_count"
                currentSort={filters.sort_by}
                currentOrder={filters.sort_order}
                onSort={handleSort}
                className="text-center"
              />
              <th className="px-3 py-2.5 text-center">Rev.</th>
              <th className="px-3 py-2.5 text-center">FB</th>
              <SortableTh
                label="Creata"
                column="created_at"
                currentSort={filters.sort_by}
                currentOrder={filters.sort_order}
                onSort={handleSort}
              />
              <th className="px-3 py-2.5">Azioni</th>
            </tr>
          </thead>
          <tbody>
            {loading && !data ? (
              <tr>
                <td colSpan={9} className="py-12 text-center text-sm text-gray-400 dark:text-gray-500">
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
                <td colSpan={9} className="py-12 text-center text-sm text-gray-400 dark:text-gray-500">
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
        <div className="border-t border-gray-100 dark:border-gray-800 px-4 py-2 text-xs text-gray-400 dark:text-gray-500">
          {data.total} {data.total === 1 ? "voce" : "voci"} totali
        </div>
      )}
    </div>
  );
}
