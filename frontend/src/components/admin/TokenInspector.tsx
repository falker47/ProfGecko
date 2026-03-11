"use client";

import { useEffect, useState } from "react";
import { debugHash, addStopwords, removeStopword } from "@/lib/admin-api";
import type { DebugHashResult } from "@/lib/admin-types";

interface TokenInspectorProps {
  question: string;
  generation: number;
  secret: string;
  onStopwordAdded: () => void;
  onAuthFailed: () => void;
}

export default function TokenInspector({
  question,
  generation,
  secret,
  onStopwordAdded,
  onAuthFailed,
}: TokenInspectorProps) {
  const [result, setResult] = useState<DebugHashResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function fetchDebug() {
      setLoading(true);
      try {
        const data = await debugHash(secret, question, generation);
        if (!cancelled) setResult(data);
      } catch (err) {
        if (err instanceof Error && err.message === "AUTH_FAILED") {
          onAuthFailed();
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchDebug();
    return () => {
      cancelled = true;
    };
  }, [question, generation, secret, onAuthFailed]);

  async function handleAddStopword(word: string) {
    setBusy(word);
    setMessage("");
    try {
      const res = await addStopwords(secret, [word]);
      setMessage(
        `"${word}" aggiunta — ${res.entries_rehashed} entry ricalcolate`,
      );
      const data = await debugHash(secret, question, generation);
      setResult(data);
      onStopwordAdded();
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      } else {
        setMessage("Errore nell'aggiunta");
      }
    } finally {
      setBusy(null);
    }
  }

  async function handleRemoveStopword(word: string) {
    setBusy(word);
    setMessage("");
    try {
      const res = await removeStopword(secret, word);
      setMessage(
        `"${word}" rimossa — ${res.entries_rehashed} entry ricalcolate`,
      );
      const data = await debugHash(secret, question, generation);
      setResult(data);
      onStopwordAdded();
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      } else {
        setMessage("Errore nella rimozione");
      }
    } finally {
      setBusy(null);
    }
  }

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-950 p-3">
        <p className="text-xs text-gray-400 dark:text-gray-500">Caricamento token...</p>
      </div>
    );
  }

  if (!result) return null;

  const tokens = result.pipeline["4_final_tokens"];
  const removedBuiltin = result.pipeline["3d_builtin_stopwords_removed"];
  const removedCustom = result.pipeline["3e_custom_stopwords_removed"];
  const removedGame = result.pipeline["3b_game_titles_removed"];

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-950 p-3">
      <p className="mb-2 text-xs font-medium uppercase text-gray-500 dark:text-gray-400">
        Token hash — clicca per rendere stopword
      </p>

      {/* Final tokens (clickable to add as stopword) */}
      <div className="mb-2 flex flex-wrap gap-1.5">
        {tokens.length > 0 ? (
          tokens.map((token) => (
            <button
              key={token}
              onClick={() => handleAddStopword(token)}
              disabled={busy !== null}
              title={`Aggiungi "${token}" come stopword`}
              className="rounded-full border border-emerald-300 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-950 px-2.5 py-1 font-mono text-xs text-emerald-800 dark:text-emerald-200 transition-colors hover:bg-red-50 dark:hover:bg-red-950 hover:border-red-300 dark:hover:border-red-700 hover:text-red-700 dark:hover:text-red-400 disabled:opacity-50"
            >
              {busy === token ? "..." : token}
            </button>
          ))
        ) : (
          <span className="text-xs text-gray-400 dark:text-gray-500">Nessun token rimasto</span>
        )}
      </div>

      {/* Removed tokens */}
      {(removedBuiltin.length > 0 ||
        removedCustom.length > 0 ||
        removedGame.length > 0) && (
        <div className="flex flex-wrap gap-1.5">
          <span className="self-center text-xs text-gray-400 dark:text-gray-500">Rimossi:</span>
          {removedBuiltin.map((token, i) => (
            <span
              key={`b-${token}-${i}`}
              className="rounded-full border border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 font-mono text-xs text-gray-400 dark:text-gray-500 line-through"
              title="Stopword built-in (non rimovibile)"
            >
              {token}
            </span>
          ))}
          {/* Custom stopwords — clickable to remove (unflag) */}
          {removedCustom.map((token, i) => (
            <button
              key={`c-${token}-${i}`}
              onClick={() => handleRemoveStopword(token)}
              disabled={busy !== null}
              title={`Rimuovi "${token}" dalle stopword`}
              className="rounded-full border border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-950 px-2.5 py-1 font-mono text-xs text-amber-600 dark:text-amber-400 line-through transition-colors hover:bg-emerald-50 dark:hover:bg-emerald-950 hover:border-emerald-300 dark:hover:border-emerald-700 hover:text-emerald-700 dark:hover:text-emerald-300 hover:no-underline disabled:opacity-50"
            >
              {busy === token ? "..." : token}
            </button>
          ))}
          {removedGame.map((token, i) => (
            <span
              key={`g-${token}-${i}`}
              className="rounded-full border border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 font-mono text-xs text-gray-400 dark:text-gray-500 line-through"
              title="Titolo gioco (non rimovibile)"
            >
              {token}
            </span>
          ))}
        </div>
      )}

      {/* Feedback message */}
      {message && (
        <p className="mt-2 text-xs text-emerald-700 dark:text-emerald-300">{message}</p>
      )}
    </div>
  );
}
