import { API_BASE_URL } from "./constants";
import type {
  CacheStats,
  EntriesResponse,
  EntriesFilters,
  CacheEntry,
  DebugHashResult,
} from "./admin-types";

// ── Helper ────────────────────────────────────────────────────────

async function adminFetch(
  secret: string,
  path: string,
  options?: RequestInit & { params?: Record<string, string> },
): Promise<Response> {
  const url = new URL(`${API_BASE_URL}${path}`);
  url.searchParams.set("secret", secret);
  if (options?.params) {
    for (const [k, v] of Object.entries(options.params)) {
      url.searchParams.set(k, v);
    }
  }
  const { params: _, ...fetchOpts } = options ?? {};
  const res = await fetch(url.toString(), {
    ...fetchOpts,
    headers: { "Content-Type": "application/json", ...fetchOpts?.headers },
  });
  if (res.status === 403) {
    throw new Error("AUTH_FAILED");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Errore: ${res.status}`);
  }
  return res;
}

// ── Stats ─────────────────────────────────────────────────────────

export async function getStats(secret: string): Promise<CacheStats> {
  const res = await adminFetch(secret, "/api/admin/cache/stats");
  return res.json();
}

// ── Entries ───────────────────────────────────────────────────────

export async function getEntries(
  secret: string,
  filters: EntriesFilters,
): Promise<EntriesResponse> {
  const params: Record<string, string> = {
    page: String(filters.page),
    per_page: String(filters.per_page),
  };
  if (filters.reviewed !== null) {
    params.reviewed = String(filters.reviewed);
  }
  if (filters.generation !== null) {
    params.generation = String(filters.generation);
  }
  if (filters.search.trim()) {
    params.search = filters.search.trim();
  }
  const res = await adminFetch(secret, "/api/admin/cache/entries", { params });
  return res.json();
}

export async function updateEntry(
  secret: string,
  entryId: number,
  response: string,
): Promise<CacheEntry> {
  const res = await adminFetch(
    secret,
    `/api/admin/cache/entries/${entryId}`,
    {
      method: "PUT",
      body: JSON.stringify({ response }),
    },
  );
  return res.json();
}

export async function approveEntry(
  secret: string,
  entryId: number,
): Promise<{ status: string; entry_id: number; reviewed: boolean }> {
  const res = await adminFetch(
    secret,
    `/api/admin/cache/entries/${entryId}/approve`,
    { method: "POST" },
  );
  return res.json();
}

// ── Debug ─────────────────────────────────────────────────────────

export async function debugHash(
  secret: string,
  question: string,
  generation: number,
): Promise<DebugHashResult> {
  const res = await adminFetch(secret, "/api/admin/cache/debug", {
    params: { question, generation: String(generation) },
  });
  return res.json();
}

// ── Bulk actions ──────────────────────────────────────────────────

export async function invalidateCache(
  secret: string,
): Promise<{ status: string; entries_deleted: number }> {
  const res = await adminFetch(secret, "/api/admin/cache/invalidate", {
    method: "POST",
  });
  return res.json();
}

export async function cleanupCache(
  secret: string,
  maxAgeDays: number = 90,
): Promise<{ status: string; stale_entries_removed: number }> {
  const res = await adminFetch(secret, "/api/admin/cache/cleanup", {
    method: "POST",
    params: { max_age_days: String(maxAgeDays) },
  });
  return res.json();
}

// ── Import CSV ───────────────────────────────────────────────────

export async function importCsv(
  secret: string,
  file: File,
): Promise<{ status: string; imported: number; skipped: number; total_in_file: number }> {
  const url = new URL(`${API_BASE_URL}/api/admin/cache/import`);
  url.searchParams.set("secret", secret);

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(url.toString(), {
    method: "POST",
    body: formData,
    // NOTE: do NOT set Content-Type — browser sets it with boundary for multipart
  });
  if (res.status === 403) {
    throw new Error("AUTH_FAILED");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Errore: ${res.status}`);
  }
  return res.json();
}

// ── Export URL (no fetch, just builds the URL) ────────────────────

export function getExportUrl(secret: string): string {
  return `${API_BASE_URL}/api/admin/cache/export?secret=${encodeURIComponent(secret)}`;
}
