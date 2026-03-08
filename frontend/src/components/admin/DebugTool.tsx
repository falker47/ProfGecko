"use client";

import { useState } from "react";
import { debugHash } from "@/lib/admin-api";
import type { DebugHashResult } from "@/lib/admin-types";

interface DebugToolProps {
  secret: string;
  onAuthFailed: () => void;
}

export default function DebugTool({ secret, onAuthFailed }: DebugToolProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [generation, setGeneration] = useState(9);
  const [result, setResult] = useState<DebugHashResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleAnalyze(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError("");

    try {
      const data = await debugHash(secret, question.trim(), generation);
      setResult(data);
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        onAuthFailed();
      } else {
        setError(err instanceof Error ? err.message : "Errore");
      }
    } finally {
      setLoading(false);
    }
  }

  const STEPS = [
    { key: "0_after_gen_split", label: "Dopo split gen" },
    { key: "1_after_ordinals", label: "Dopo ordinali" },
    { key: "2_after_plurals", label: "Dopo plurali" },
    { key: "3_gen_numbers_removed", label: "Indici gen rimossi" },
    { key: "4_final_tokens", label: "Token finali" },
    { key: "5_hash_input", label: "Input hash" },
  ] as const;

  return (
    <div className="rounded-xl bg-white shadow-sm">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="text-sm font-medium text-gray-700">
          🔍 Strumento Debug Hash
        </span>
        <span className="text-gray-400">{isOpen ? "▲" : "▼"}</span>
      </button>

      {isOpen && (
        <div className="border-t border-gray-200 px-4 py-4">
          <form onSubmit={handleAnalyze} className="flex flex-wrap items-end gap-3">
            <div className="min-w-[250px] flex-1">
              <label className="mb-1 block text-xs font-medium text-gray-500">
                Domanda
              </label>
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="es. debolezze garchomp gen 4"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 placeholder-gray-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">
                Gen
              </label>
              <select
                value={generation}
                onChange={(e) => setGeneration(Number(e.target.value))}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              >
                {Array.from({ length: 9 }, (_, i) => i + 1).map((g) => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "..." : "Analizza"}
            </button>
          </form>

          {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

          {result && (
            <div className="mt-4 space-y-3">
              <div className="flex flex-wrap gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Exact hash: </span>
                  <code className="rounded bg-gray-100 px-2 py-0.5 font-mono text-xs">
                    {result.exact_hash}
                  </code>
                </div>
                <div>
                  <span className="text-gray-500">Normal hash: </span>
                  <code className="rounded bg-gray-100 px-2 py-0.5 font-mono text-xs">
                    {result.normal_hash}
                  </code>
                </div>
              </div>

              <div className="rounded-lg bg-gray-50 p-3">
                <p className="mb-2 text-xs font-medium text-gray-500 uppercase">
                  Pipeline di normalizzazione
                </p>
                <dl className="space-y-1.5 text-sm">
                  {STEPS.map(({ key, label }) => {
                    const value = result.pipeline[key];
                    const display = Array.isArray(value)
                      ? value.length > 0
                        ? value.join(", ")
                        : "—"
                      : value || "—";
                    return (
                      <div key={key} className="flex gap-2">
                        <dt className="w-44 shrink-0 text-gray-500">{label}:</dt>
                        <dd className="font-mono text-gray-800">{display}</dd>
                      </div>
                    );
                  })}
                </dl>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
