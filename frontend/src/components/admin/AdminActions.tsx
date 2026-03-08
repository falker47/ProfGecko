"use client";

import { useState } from "react";
import { invalidateCache, cleanupCache, getExportUrl } from "@/lib/admin-api";

interface AdminActionsProps {
  secret: string;
  onAction: () => void;
  onAuthFailed: () => void;
}

export default function AdminActions({
  secret,
  onAction,
  onAuthFailed,
}: AdminActionsProps) {
  const [message, setMessage] = useState("");

  function showMessage(text: string) {
    setMessage(text);
    setTimeout(() => setMessage(""), 4000);
  }

  async function handleInvalidate() {
    if (!confirm("Sei sicuro? Verranno eliminate tutte le voci non revisionate.")) {
      return;
    }
    try {
      const res = await invalidateCache(secret);
      showMessage(`${res.entries_deleted} voci eliminate`);
      onAction();
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      } else {
        showMessage("Errore nell'invalidazione");
      }
    }
  }

  async function handleCleanup() {
    if (!confirm("Eliminare le voci non revisionate più vecchie di 90 giorni?")) {
      return;
    }
    try {
      const res = await cleanupCache(secret, 90);
      showMessage(`${res.stale_entries_removed} voci obsolete rimosse`);
      onAction();
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      } else {
        showMessage("Errore nella pulizia");
      }
    }
  }

  function handleExport() {
    window.open(getExportUrl(secret), "_blank");
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        onClick={handleInvalidate}
        className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700"
      >
        Invalida Cache
      </button>

      <button
        onClick={handleCleanup}
        className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-600"
      >
        Pulizia Vecchie
      </button>

      <button
        onClick={handleExport}
        className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700"
      >
        Esporta CSV
      </button>

      {message && (
        <span className="rounded-lg bg-gray-800 px-3 py-1.5 text-sm text-white">
          {message}
        </span>
      )}
    </div>
  );
}
