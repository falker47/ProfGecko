"use client";

import { useEffect, useState } from "react";
import { debugHash, addStopwords } from "@/lib/admin-api";
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
  const [adding, setAdding] = useState<string | null>(null);
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
    setAdding(word);
    setMessage("");
    try {
      const res = await addStopwords(secret, [word]);
      setMessage(
        `"${word}" aggiunta — ${res.entries_rehashed} entry ricalcolate`,
      );
      // Re-fetch debug to show updated pipeline
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
      setAdding(null);
    }
  }

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
        <p className="text-xs text-gray-400">Caricamento token...</p>
      </div>
    );
  }

  if (!result) return null;

  const tokens = result.pipeline["4_final_tokens"];
  const removedBuiltin = result.pipeline["3d_builtin_stopwords_removed"];
  const removedCustom = result.pipeline["3e_custom_stopwords_removed"];
  const removedGame = result.pipeline["3b_game_titles_removed"];

  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
      <p className="mb-2 text-xs font-medium uppercase text-gray-500">
        Token hash — clicca per rendere stopword
      </p>

      {/* Final tokens (clickable to add as stopword) */}
      <div className="mb-2 flex flex-wrap gap-1.5">
        {tokens.length > 0 ? (
          tokens.map((token) => (
            <button
              key={token}
              onClick={() => handleAddStopword(token)}
              disabled={adding !== null}
              title={`Aggiungi "${token}" come stopword`}
              className="rounded-full border border-emerald-300 bg-emerald-50 px-2.5 py-1 font-mono text-xs text-emerald-800 transition-colors hover:bg-red-50 hover:border-red-300 hover:text-red-700 disabled:opacity-50"
            >
              {adding === token ? "..." : token}
            </button>
          ))
        ) : (
          <span className="text-xs text-gray-400">Nessun token rimasto</span>
        )}
      </div>

      {/* Removed tokens (readonly, for info) */}
      {(removedBuiltin.length > 0 ||
        removedCustom.length > 0 ||
        removedGame.length > 0) && (
        <div className="flex flex-wrap gap-1.5">
          <span className="self-center text-xs text-gray-400">Rimossi:</span>
          {removedBuiltin.map((token, i) => (
            <span
              key={`b-${token}-${i}`}
              className="rounded-full border border-gray-200 bg-gray-100 px-2 py-0.5 font-mono text-xs text-gray-400 line-through"
              title="Stopword built-in"
            >
              {token}
            </span>
          ))}
          {removedCustom.map((token, i) => (
            <span
              key={`c-${token}-${i}`}
              className="rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 font-mono text-xs text-amber-600 line-through"
              title="Stopword personalizzata"
            >
              {token}
            </span>
          ))}
          {removedGame.map((token, i) => (
            <span
              key={`g-${token}-${i}`}
              className="rounded-full border border-gray-200 bg-gray-100 px-2 py-0.5 font-mono text-xs text-gray-400 line-through"
              title="Titolo gioco"
            >
              {token}
            </span>
          ))}
        </div>
      )}

      {/* Feedback message */}
      {message && (
        <p className="mt-2 text-xs text-emerald-700">{message}</p>
      )}
    </div>
  );
}
