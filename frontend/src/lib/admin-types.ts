// ── Admin panel types ─────────────────────────────────────────────

export interface CacheEntry {
  id: number;
  question: string;
  generation: number;
  response: string;
  hit_count: number;
  reviewed: boolean;
  created_at: string;
  last_hit_at: string | null;
  reviewed_at: string | null;
  exact_hash: string;
  normal_hash: string;
  feedback: string;
}

export interface EntriesResponse {
  entries: CacheEntry[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface CacheStats {
  total_entries: number;
  total_hits: number;
  reviewed_entries: number;
}

export interface DebugHashResult {
  question: string;
  generation: number;
  exact_hash: string;
  normal_hash: string;
  pipeline: {
    "0_after_gen_split": string[];
    "1_after_ordinals": string[];
    "2_after_plurals": string[];
    "3_gen_numbers_removed": number[];
    "3b_game_titles_removed": string[];
    "3c_conditional_removed": string[];
    "3d_builtin_stopwords_removed": string[];
    "3e_custom_stopwords_removed": string[];
    "4_final_tokens": string[];
    "5_hash_input": string;
  };
}

export interface StopwordsResponse {
  words: string[];
  total: number;
}

export interface AddStopwordsResult {
  status: string;
  stopwords_added: number;
  stopwords_total: number;
  entries_rehashed: number;
  duplicates_found: number;
}

export interface RemoveStopwordResult {
  status: string;
  word_removed: string;
  entries_rehashed: number;
}

export interface EntriesFilters {
  page: number;
  per_page: number;
  reviewed: boolean | null;
  generation: number | null;
  search: string;
}
