"use client";

import { useRef, useState } from "react";
import { invalidateCache, cleanupCache, rehashCache, getExportUrl, importCsv, reloadVectorstore } from "@/lib/admin-api";

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
  const [importing, setImporting] = useState(false);
  const [reloading, setReloading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function showMessage(text: string, duration = 5000) {
    setMessage(text);
    setTimeout(() => setMessage(""), duration);
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

  async function handleRehash() {
    if (!confirm("Ricalcolare tutti gli hash della cache? Le entry esistenti verranno aggiornate.")) {
      return;
    }
    try {
      const res = await rehashCache(secret);
      let msg = `${res.entries_updated} hash aggiornati, ${res.duplicates_found} duplicati trovati`;
      if (res.duplicates && res.duplicates.length > 0) {
        const details = res.duplicates
          .map((d) => `#${d.id} "${d.question}" (gen${d.generation}, dup di #${d.duplicate_of_id}, hash=${d.normal_hash})`)
          .join(" | ");
        msg += ` → ${details}`;
      }
      showMessage(msg, res.duplicates_found > 0 ? 30000 : 5000);
      onAction();
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      } else {
        showMessage("Errore nel rehash");
      }
    }
  }

  function handleExport() {
    window.open(getExportUrl(secret), "_blank");
  }

  async function handleImportFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setImporting(true);
    try {
      const res = await importCsv(secret, file);
      showMessage(
        `Importate ${res.imported} voci, ${res.skipped} duplicate saltate (${res.total_in_file} nel file)`,
      );
      onAction();
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      } else {
        showMessage(err instanceof Error ? err.message : "Errore nell'importazione");
      }
    } finally {
      setImporting(false);
      // Reset file input so the same file can be re-selected
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleReloadVectorstore() {
    if (!confirm("Ricaricare il vectorstore dal disco? Usalo dopo aver eseguito run_ingestion.bat.")) {
      return;
    }
    setReloading(true);
    try {
      const res = await reloadVectorstore(secret);
      showMessage(`Vectorstore ricaricato: ${res.documents_loaded.toLocaleString("it-IT")} documenti`);
      onAction();
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      } else {
        showMessage("Errore nel ricaricamento del vectorstore");
      }
    } finally {
      setReloading(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        onClick={handleReloadVectorstore}
        disabled={reloading}
        className={`rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-700 ${
          reloading ? "cursor-not-allowed opacity-50" : ""
        }`}
      >
        {reloading ? "Ricaricamento..." : "⟳ Ricarica Vectorstore"}
      </button>

      <div className="h-6 w-px bg-gray-300" />

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
        onClick={handleRehash}
        className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-700"
      >
        Rehash
      </button>

      <button
        onClick={handleExport}
        className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700"
      >
        Esporta CSV
      </button>

      <label
        className={`cursor-pointer rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 ${
          importing ? "cursor-not-allowed opacity-50" : ""
        }`}
      >
        {importing ? "Importazione..." : "Importa CSV"}
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleImportFile}
          disabled={importing}
          className="hidden"
        />
      </label>

      {message && (
        <span className="rounded-lg bg-gray-800 px-3 py-1.5 text-sm text-white">
          {message}
        </span>
      )}
    </div>
  );
}
