"use client";

import { useState } from "react";
import { getStats } from "@/lib/admin-api";

interface AdminLoginProps {
  onLogin: (secret: string) => void;
}

export default function AdminLogin({ onLogin }: AdminLoginProps) {
  const [secret, setSecret] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!secret.trim()) return;

    setLoading(true);
    setError("");

    try {
      await getStats(secret.trim());
      onLogin(secret.trim());
    } catch (err) {
      if (err instanceof Error && err.message === "AUTH_FAILED") {
        setError("Chiave segreta non valida");
      } else {
        setError("Errore di connessione al server");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
        <div className="mb-8 text-center">
          <div className="mb-2 text-4xl">🗡️</div>
          <h1 className="text-2xl font-bold text-gray-900">Pannello Admin</h1>
          <p className="mt-1 text-sm text-gray-500">Prof. Gallade</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="secret"
              className="mb-1 block text-sm font-medium text-gray-700"
            >
              Chiave segreta
            </label>
            <input
              id="secret"
              type="password"
              value={secret}
              onChange={(e) => setSecret(e.target.value)}
              placeholder="Inserisci la chiave segreta..."
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 placeholder-gray-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              autoFocus
            />
          </div>

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading || !secret.trim()}
            className="w-full rounded-lg bg-emerald-600 px-4 py-2.5 font-medium text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Verifica in corso..." : "Accedi"}
          </button>
        </form>
      </div>
    </div>
  );
}
