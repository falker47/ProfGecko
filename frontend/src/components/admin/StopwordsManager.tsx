"use client";

import { useCallback, useEffect, useState } from "react";
import { listStopwords, addStopwords, removeStopword } from "@/lib/admin-api";

interface StopwordsManagerProps {
  secret: string;
  onChanged: () => void;
  onAuthFailed: () => void;
  refreshKey: number;
}

export default function StopwordsManager({
  secret,
  onChanged,
  onAuthFailed,
  refreshKey,
}: StopwordsManagerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [words, setWords] = useState<string[]>([]);
  const [newWord, setNewWord] = useState("");
  const [loading, setLoading] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  const fetchWords = useCallback(async () => {
    try {
      const data = await listStopwords(secret);
      setWords(data.words);
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      }
    }
  }, [secret, onAuthFailed]);

  useEffect(() => {
    if (isOpen) fetchWords();
  }, [isOpen, fetchWords, refreshKey]);

  function showMessage(text: string) {
    setMessage(text);
    setTimeout(() => setMessage(""), 5000);
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = newWord.trim().toLowerCase();
    if (!trimmed) return;

    setLoading(true);
    try {
      const res = await addStopwords(secret, [trimmed]);
      setNewWord("");
      showMessage(
        `"${trimmed}" aggiunta — ${res.entries_rehashed} entry ricalcolate`,
      );
      await fetchWords();
      onChanged();
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      } else {
        showMessage("Errore nell'aggiunta");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleRemove(word: string) {
    setRemoving(word);
    try {
      const res = await removeStopword(secret, word);
      showMessage(
        `"${word}" rimossa — ${res.entries_rehashed} entry ricalcolate`,
      );
      await fetchWords();
      onChanged();
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      } else {
        showMessage("Errore nella rimozione");
      }
    } finally {
      setRemoving(null);
    }
  }

  return (
    <div className="rounded-xl bg-white dark:bg-gray-900 shadow-sm">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          🛑 Stopword personalizzate
          {words.length > 0 && (
            <span className="ml-2 rounded-full bg-amber-100 dark:bg-amber-900 px-2 py-0.5 text-xs text-amber-700 dark:text-amber-300">
              {words.length}
            </span>
          )}
        </span>
        <span className="text-gray-400 dark:text-gray-500">{isOpen ? "▲" : "▼"}</span>
      </button>

      {isOpen && (
        <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-4">
          {/* Add form */}
          <form onSubmit={handleAdd} className="mb-4 flex gap-2">
            <input
              type="text"
              value={newWord}
              onChange={(e) => setNewWord(e.target.value)}
              placeholder="Aggiungi stopword..."
              className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 text-sm text-gray-700 dark:text-gray-100 dark:bg-gray-800 placeholder-gray-400 dark:placeholder-gray-500 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
            />
            <button
              type="submit"
              disabled={loading || !newWord.trim()}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "..." : "Aggiungi"}
            </button>
          </form>

          {/* Word list */}
          {words.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {words.map((word) => (
                <span
                  key={word}
                  className="group flex items-center gap-1 rounded-full border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950 px-3 py-1 text-sm text-amber-800 dark:text-amber-200"
                >
                  <span className="font-mono">{word}</span>
                  <button
                    onClick={() => handleRemove(word)}
                    disabled={removing !== null}
                    title={`Rimuovi "${word}"`}
                    className="ml-0.5 rounded-full text-amber-400 transition-colors hover:text-red-600 disabled:opacity-50"
                  >
                    ✕
                  </button>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 dark:text-gray-500">
              Nessuna stopword personalizzata. Aggiungi parole qui o clicca i
              token nelle righe della tabella.
            </p>
          )}

          {/* Feedback */}
          {message && (
            <p className="mt-3 rounded-lg bg-gray-800 dark:bg-gray-700 px-3 py-1.5 text-sm text-white">
              {message}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
