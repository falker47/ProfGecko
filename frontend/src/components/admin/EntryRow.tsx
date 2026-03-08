"use client";

import { useState } from "react";
import clsx from "clsx";
import ReactMarkdown from "react-markdown";
import { approveEntry } from "@/lib/admin-api";
import type { CacheEntry } from "@/lib/admin-types";
import EntryEditor from "./EntryEditor";

interface EntryRowProps {
  entry: CacheEntry;
  expanded: boolean;
  onToggle: () => void;
  secret: string;
  onUpdated: () => void;
  onAuthFailed: () => void;
}

function truncate(str: string, max: number): string {
  return str.length > max ? str.slice(0, max) + "…" : str;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
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

export default function EntryRow({
  entry,
  expanded,
  onToggle,
  secret,
  onUpdated,
  onAuthFailed,
}: EntryRowProps) {
  const [approving, setApproving] = useState(false);

  async function handleApprove(e: React.MouseEvent) {
    e.stopPropagation();
    setApproving(true);
    try {
      await approveEntry(secret, entry.id);
      onUpdated();
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      }
    } finally {
      setApproving(false);
    }
  }

  return (
    <>
      {/* Riga collassata */}
      <tr
        onClick={onToggle}
        className={clsx(
          "cursor-pointer border-b border-gray-100 transition-colors hover:bg-gray-50",
          entry.reviewed && "border-l-4 border-l-emerald-400",
          expanded && "bg-emerald-50/50",
        )}
      >
        <td className="px-3 py-2.5 text-xs text-gray-400">{entry.id}</td>
        <td className="max-w-[250px] px-3 py-2.5 text-sm text-gray-800">
          {truncate(entry.question, 50)}
        </td>
        <td className="px-3 py-2.5 text-center text-sm text-gray-600">
          {entry.generation}
        </td>
        <td className="max-w-[300px] px-3 py-2.5 text-sm text-gray-600">
          {truncate(entry.response, 60)}
        </td>
        <td className="px-3 py-2.5 text-center text-sm text-gray-600">
          {entry.hit_count}
        </td>
        <td className="px-3 py-2.5 text-center">
          {entry.reviewed ? (
            <span className="text-emerald-600" title="Revisionata">✓</span>
          ) : (
            <span className="text-gray-300" title="Non revisionata">✗</span>
          )}
        </td>
        <td className="px-3 py-2.5 text-xs text-gray-400">
          {formatDate(entry.created_at)}
        </td>
        <td className="px-3 py-2.5">
          {!entry.reviewed && (
            <button
              onClick={handleApprove}
              disabled={approving}
              className="rounded bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-700 transition-colors hover:bg-emerald-200 disabled:opacity-50"
            >
              {approving ? "..." : "Approva"}
            </button>
          )}
        </td>
      </tr>

      {/* Riga espansa */}
      {expanded && (
        <tr className="border-b border-gray-200 bg-gray-50/80">
          <td colSpan={8} className="px-4 py-4">
            <div className="space-y-4">
              {/* Domanda completa */}
              <div>
                <p className="mb-1 text-xs font-medium text-gray-500 uppercase">
                  Domanda
                </p>
                <p className="text-sm text-gray-800">{entry.question}</p>
              </div>

              {/* Risposta completa (markdown) */}
              <div>
                <p className="mb-1 text-xs font-medium text-gray-500 uppercase">
                  Risposta attuale
                </p>
                <div className="rounded-lg bg-white p-3 text-sm text-gray-800 prose prose-sm max-w-none">
                  <ReactMarkdown>{entry.response}</ReactMarkdown>
                </div>
              </div>

              {/* Metadati */}
              <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-400">
                <span>Exact hash: <code className="font-mono">{entry.exact_hash}</code></span>
                <span>Normal hash: <code className="font-mono">{entry.normal_hash}</code></span>
                <span>Creata: {formatDate(entry.created_at)}</span>
                <span>Ultimo hit: {formatDate(entry.last_hit_at)}</span>
                <span>Revisionata: {formatDate(entry.reviewed_at)}</span>
              </div>

              {/* Editor */}
              <EntryEditor
                entry={entry}
                secret={secret}
                onSaved={onUpdated}
                onAuthFailed={onAuthFailed}
              />
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
