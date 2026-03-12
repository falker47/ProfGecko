"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { invalidateCache, cleanupCache, rehashCache, exportCsv, importCsv, reloadVectorstore, startIngestion, getIngestionStatus } from "@/lib/admin-api";
import type { IngestionStatus } from "@/lib/admin-api";

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
  const [ingesting, setIngesting] = useState(false);
  const [ingestProgress, setIngestProgress] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  function showMessage(text: string, duration = 5000) {
    setMessage(text);
    setTimeout(() => setMessage(""), duration);
  }

  const stopTimer = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  }, []);

  const startTimer = useCallback((offsetSeconds = 0) => {
    stopTimer();
    startTimeRef.current = Date.now() - offsetSeconds * 1000;
    timerRef.current = setInterval(() => {
      const secs = Math.round((Date.now() - startTimeRef.current) / 1000);
      setIngestProgress(`In corso... ${secs}s`);
    }, 1000);
  }, [stopTimer]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  // Check if ingestion is already running on mount
  useEffect(() => {
    async function checkRunning() {
      try {
        const status = await getIngestionStatus(secret);
        if (status.status === "running") {
          setIngesting(true);
          startTimer(status.elapsed_seconds ?? 0);
          startPolling();
        }
      } catch {
        // ignore — panel just opened
      }
    }
    checkRunning();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [secret]);

  const startPolling = useCallback(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const status: IngestionStatus = await getIngestionStatus(secret);
        if (status.status === "completed") {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          stopTimer();
          setIngesting(false);
          setIngestProgress("");
          const docs = status.documents_indexed ?? 0;
          const secs = Math.round(status.elapsed_seconds ?? 0);
          showMessage(
            `Ingestione completata: ${docs.toLocaleString("it-IT")} documenti in ${secs}s`,
            10000,
          );
          onAction();
        } else if (status.status === "error") {
          if (pollRef.current) clearInterval(pollRef.current);
          pollRef.current = null;
          stopTimer();
          setIngesting(false);
          setIngestProgress("");
          showMessage(
            `Errore ingestione: ${status.error ?? "errore sconosciuto"}`,
            15000,
          );
        }
      } catch {
        // network error, keep polling — local timer keeps ticking
      }
    }, 5000);
  }, [secret, onAction, stopTimer]);

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

  async function handleExport() {
    try {
      const blob = await exportCsv(secret);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "cache_entries.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      } else {
        showMessage("Errore nell'export");
      }
    }
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

  async function handleStartIngestion() {
    if (
      !confirm(
        "Avviare la re-ingestione completa? Questo processo richiede 10-15 minuti e ricostruisce l'intero vectorstore.",
      )
    ) {
      return;
    }
    setIngesting(true);
    setIngestProgress("Avvio...");
    try {
      const res = await startIngestion(secret, true);
      if (res.status === "already_running") {
        showMessage("Ingestione già in corso!");
      } else {
        showMessage("Ingestione avviata in background");
      }
      startTimer();
      startPolling();
    } catch (err) {
      stopTimer();
      setIngesting(false);
      setIngestProgress("");
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      } else {
        showMessage("Errore nell'avvio dell'ingestione");
      }
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
        onClick={handleStartIngestion}
        disabled={ingesting}
        className={`rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-teal-700 ${
          ingesting ? "cursor-not-allowed opacity-50" : ""
        }`}
      >
        {ingesting ? `🔄 ${ingestProgress}` : "🚀 Avvia Ingestione"}
      </button>

      <button
        onClick={handleReloadVectorstore}
        disabled={reloading}
        className={`rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-700 ${
          reloading ? "cursor-not-allowed opacity-50" : ""
        }`}
      >
        {reloading ? "Ricaricamento..." : "⟳ Ricarica Vectorstore"}
      </button>

      <div className="h-6 w-px bg-gray-300 dark:bg-gray-600" />

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
        <span className="rounded-lg bg-gray-800 dark:bg-gray-700 px-3 py-1.5 text-sm text-white">
          {message}
        </span>
      )}
    </div>
  );
}
