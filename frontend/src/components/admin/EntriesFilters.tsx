"use client";

import { useRef, useState } from "react";
import type { EntriesFilters as Filters } from "@/lib/admin-types";

interface EntriesFiltersProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

export default function EntriesFilters({ filters, onChange }: EntriesFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.search);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  function update(patch: Partial<Filters>) {
    onChange({ ...filters, page: 1, ...patch });
  }

  function handleSearchChange(value: string) {
    setSearchInput(value);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      update({ search: value });
    }, 300);
  }

  return (
    <div className="flex flex-wrap items-center gap-3 border-b border-gray-200 px-4 py-3">
      {/* Generazione */}
      <select
        value={filters.generation ?? ""}
        onChange={(e) =>
          update({ generation: e.target.value ? Number(e.target.value) : null })
        }
        className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
      >
        <option value="">Tutte le gen</option>
        {Array.from({ length: 9 }, (_, i) => i + 1).map((g) => (
          <option key={g} value={g}>
            Gen {g}
          </option>
        ))}
      </select>

      {/* Stato revisione */}
      <select
        value={filters.reviewed === null ? "" : String(filters.reviewed)}
        onChange={(e) => {
          const v = e.target.value;
          update({ reviewed: v === "" ? null : v === "true" });
        }}
        className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
      >
        <option value="">Tutti</option>
        <option value="true">Revisionate</option>
        <option value="false">Non revisionate</option>
      </select>

      {/* Feedback */}
      <select
        value={filters.feedback ?? ""}
        onChange={(e) =>
          update({ feedback: e.target.value || null })
        }
        className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
      >
        <option value="">Tutti i FB</option>
        <option value="V">✓ Corretta</option>
        <option value="F">✗ Errata</option>
        <option value="M">⚠ Missing</option>
        <option value="-">— Nessuno</option>
      </select>

      {/* Ricerca */}
      <input
        type="text"
        value={searchInput}
        onChange={(e) => handleSearchChange(e.target.value)}
        placeholder="Cerca nella domanda..."
        className="min-w-[200px] flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 placeholder-gray-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
      />
    </div>
  );
}
