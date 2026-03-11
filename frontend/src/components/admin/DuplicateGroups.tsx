"use client";

import { useCallback, useEffect, useState } from "react";
import { getDuplicateGroups, deleteEntry } from "@/lib/admin-api";
import type { DuplicateGroupsResponse, DuplicateGroup } from "@/lib/admin-types";

interface DuplicateGroupsProps {
  secret: string;
  onChanged: () => void;
  onAuthFailed: () => void;
  refreshKey: number;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "\u2014";
  try {
    return new Date(dateStr + "Z").toLocaleDateString("it-IT", {
      day: "2-digit",
      month: "2-digit",
      year: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

/* ── Single duplicate group card ──────────────────────────────── */

function GroupCard({
  group,
  secret,
  onDeleted,
  onAuthFailed,
}: {
  group: DuplicateGroup;
  secret: string;
  onDeleted: () => void;
  onAuthFailed: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [deletingAll, setDeletingAll] = useState(false);

  /** Pick the "best" entry: reviewed > feedback V > most hits > newest */
  function bestEntryId(): number {
    const sorted = [...group.entries].sort((a, b) => {
      // reviewed first
      if (a.reviewed !== b.reviewed) return a.reviewed ? -1 : 1;
      // feedback V > others
      if (a.feedback !== b.feedback) {
        if (a.feedback === "V") return -1;
        if (b.feedback === "V") return 1;
      }
      // more hits
      if (a.hit_count !== b.hit_count) return b.hit_count - a.hit_count;
      // newer
      return b.id - a.id;
    });
    return sorted[0].id;
  }

  async function handleDeleteOne(id: number) {
    if (!confirm(`Eliminare la entry #${id}?`)) return;
    setDeleting(id);
    try {
      await deleteEntry(secret, id);
      onDeleted();
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      }
    } finally {
      setDeleting(null);
    }
  }

  async function handleKeepBest() {
    const keepId = bestEntryId();
    const toDelete = group.entries.filter((e) => e.id !== keepId);
    if (
      !confirm(
        `Tenere #${keepId} ed eliminare ${toDelete.length} ${toDelete.length === 1 ? "copia" : "copie"}?`,
      )
    )
      return;

    setDeletingAll(true);
    try {
      for (const entry of toDelete) {
        await deleteEntry(secret, entry.id);
      }
      onDeleted();
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      }
    } finally {
      setDeletingAll(false);
    }
  }

  const best = bestEntryId();

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      {/* Group header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-800"
      >
        <span className="text-gray-400 dark:text-gray-500">{expanded ? "\u25BC" : "\u25B6"}</span>

        <span className="rounded bg-indigo-100 dark:bg-indigo-900 px-2 py-0.5 text-xs font-mono text-indigo-700 dark:text-indigo-300">
          Gen {group.generation}
        </span>

        <span className="flex flex-wrap gap-1">
          {group.final_tokens.map((token) => (
            <span
              key={token}
              className="rounded-full bg-gray-100 dark:bg-gray-800 px-2 py-0.5 text-xs font-mono text-gray-600 dark:text-gray-400"
            >
              {token}
            </span>
          ))}
        </span>

        <span className="ml-auto rounded-full bg-red-100 dark:bg-red-900 px-2 py-0.5 text-xs font-medium text-red-700 dark:text-red-400">
          {group.entries.length} entry
        </span>
      </button>

      {/* Expanded entries */}
      {expanded && (
        <div className="border-t border-gray-200 dark:border-gray-700">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100 dark:border-gray-800 text-xs font-medium uppercase text-gray-400 dark:text-gray-500">
                  <th className="px-3 py-2">ID</th>
                  <th className="px-3 py-2">Domanda</th>
                  <th className="px-3 py-2 text-center">Hit</th>
                  <th className="px-3 py-2 text-center">Rev.</th>
                  <th className="px-3 py-2 text-center">FB</th>
                  <th className="px-3 py-2">Creata</th>
                  <th className="px-3 py-2">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {group.entries.map((entry) => {
                  const isBest = entry.id === best;
                  return (
                    <tr
                      key={entry.id}
                      className={`border-b border-gray-50 dark:border-gray-800 ${isBest ? "bg-emerald-50/50 dark:bg-emerald-950/50" : ""}`}
                    >
                      <td className="px-3 py-2 text-xs text-gray-400 dark:text-gray-500">
                        {entry.id}
                        {isBest && (
                          <span
                            className="ml-1 text-emerald-600"
                            title="Migliore candidato"
                          >
                            *
                          </span>
                        )}
                      </td>
                      <td className="max-w-[350px] px-3 py-2 text-gray-800 dark:text-gray-200">
                        {entry.question}
                      </td>
                      <td className="px-3 py-2 text-center text-gray-600 dark:text-gray-400">
                        {entry.hit_count}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {entry.reviewed ? (
                          <span className="text-emerald-600" title="Revisionata">
                            \u2713
                          </span>
                        ) : (
                          <span className="text-gray-300 dark:text-gray-600" title="Non revisionata">
                            \u2717
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-center">
                        {entry.feedback === "V" && (
                          <span className="text-emerald-600" title="Corretta">
                            \u2713
                          </span>
                        )}
                        {entry.feedback === "F" && (
                          <span className="text-red-500" title="Errata">
                            \u2717
                          </span>
                        )}
                        {entry.feedback === "M" && (
                          <span className="text-amber-500" title="Missing">
                            \u26A0
                          </span>
                        )}
                        {entry.feedback === "-" && (
                          <span className="text-gray-300 dark:text-gray-600" title="Nessun feedback">
                            \u2014
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-xs text-gray-400 dark:text-gray-500">
                        {formatDate(entry.created_at)}
                      </td>
                      <td className="px-3 py-2">
                        <button
                          onClick={() => handleDeleteOne(entry.id)}
                          disabled={deleting !== null || deletingAll}
                          className="rounded bg-red-50 dark:bg-red-950 px-2 py-1 text-xs font-medium text-red-600 dark:text-red-400 transition-colors hover:bg-red-100 dark:hover:bg-red-900 disabled:opacity-50"
                          title="Elimina entry"
                        >
                          {deleting === entry.id ? "..." : "\u2715"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Bulk action */}
          <div className="flex items-center gap-3 border-t border-gray-100 dark:border-gray-800 px-4 py-3">
            <button
              onClick={handleKeepBest}
              disabled={deletingAll || deleting !== null}
              className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {deletingAll
                ? "Eliminazione..."
                : `Tieni #${best}, elimina ${group.entries.length - 1} ${group.entries.length - 1 === 1 ? "copia" : "copie"}`}
            </button>
            <span className="text-xs text-gray-400 dark:text-gray-500">
              Hash:{" "}
              <code className="font-mono">
                {group.normal_hash.slice(0, 12)}...
              </code>
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Main component ───────────────────────────────────────────── */

export default function DuplicateGroups({
  secret,
  onChanged,
  onAuthFailed,
  refreshKey,
}: DuplicateGroupsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [data, setData] = useState<DuplicateGroupsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const fetchGroups = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getDuplicateGroups(secret, page);
      setData(result);
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      } else {
        const msg = err instanceof Error ? err.message : "Errore sconosciuto";
        setError(msg);
        console.error("DuplicateGroups fetch error:", err);
      }
    } finally {
      setLoading(false);
    }
  }, [secret, page, onAuthFailed]);

  useEffect(() => {
    if (isOpen) fetchGroups();
  }, [isOpen, fetchGroups, refreshKey]);

  function handleDeleted() {
    fetchGroups();
    onChanged();
  }

  const totalPages = data ? Math.ceil(data.total_groups / 20) : 1;

  return (
    <div className="rounded-xl bg-white dark:bg-gray-900 shadow-sm">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {"\uD83D\uDD04"} Gruppi duplicati
          {data && data.total_groups > 0 && (
            <span className="ml-2 rounded-full bg-red-100 dark:bg-red-900 px-2 py-0.5 text-xs text-red-700 dark:text-red-400">
              {data.total_groups}
            </span>
          )}
        </span>
        <span className="text-gray-400 dark:text-gray-500">{isOpen ? "\u25B2" : "\u25BC"}</span>
      </button>

      {isOpen && (
        <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-4">
          {error ? (
            <div className="rounded-lg bg-red-50 dark:bg-red-950 px-4 py-3 text-sm text-red-700 dark:text-red-400">
              Errore: {error}
            </div>
          ) : loading && !data ? (
            <p className="py-6 text-center text-sm text-gray-400 dark:text-gray-500">
              Caricamento...
            </p>
          ) : data && data.groups.length > 0 ? (
            <div className="space-y-3">
              {data.groups.map((group) => (
                <GroupCard
                  key={`${group.normal_hash}-${group.generation}`}
                  group={group}
                  secret={secret}
                  onDeleted={handleDeleted}
                  onAuthFailed={onAuthFailed}
                />
              ))}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 pt-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="rounded border border-gray-300 dark:border-gray-600 px-3 py-1 text-xs text-gray-600 dark:text-gray-400 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40"
                  >
                    \u25C0 Prec.
                  </button>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Pagina {page} di {totalPages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="rounded border border-gray-300 dark:border-gray-600 px-3 py-1 text-xs text-gray-600 dark:text-gray-400 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40"
                  >
                    Succ. \u25B6
                  </button>
                </div>
              )}

              <p className="text-xs text-gray-400 dark:text-gray-500">
                {data.total_groups}{" "}
                {data.total_groups === 1 ? "gruppo" : "gruppi"} con hash
                duplicato
              </p>
            </div>
          ) : (
            <div className="py-6 text-center text-sm text-gray-400 dark:text-gray-500">
              <p>Nessun duplicato trovato</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
