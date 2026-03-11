"use client";

import { useState } from "react";
import { updateEntry } from "@/lib/admin-api";
import type { CacheEntry } from "@/lib/admin-types";

interface EntryEditorProps {
  entry: CacheEntry;
  secret: string;
  onSaved: () => void;
  onAuthFailed: () => void;
}

export default function EntryEditor({
  entry,
  secret,
  onSaved,
  onAuthFailed,
}: EntryEditorProps) {
  const [text, setText] = useState(entry.response);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const hasChanges = text !== entry.response;

  async function handleSave() {
    if (!hasChanges) return;
    setSaving(true);
    setError("");

    try {
      await updateEntry(secret, entry.id, text);
      onSaved();
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      } else {
        setError(err instanceof Error ? err.message : "Errore nel salvataggio");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mt-3 space-y-3">
      <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
        Modifica risposta
      </label>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        className="w-full min-h-[200px] rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 font-mono text-sm text-gray-800 dark:text-gray-100 dark:bg-gray-800 dark:placeholder-gray-500 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
      />

      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={saving || !hasChanges}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? "Salvataggio..." : "Salva e Revisiona"}
        </button>
        <button
          onClick={() => setText(entry.response)}
          disabled={!hasChanges}
          className="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Annulla
        </button>
      </div>
    </div>
  );
}
