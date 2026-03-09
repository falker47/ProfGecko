CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    google_id   TEXT UNIQUE NOT NULL,
    email       TEXT NOT NULL,
    name        TEXT NOT NULL,
    picture_url TEXT DEFAULT '',
    paid_credits INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS credit_transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT NOT NULL REFERENCES users(id),
    amount          INTEGER NOT NULL,
    type            TEXT NOT NULL,
    balance_after   INTEGER NOT NULL,
    stripe_session_id TEXT DEFAULT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tx_user ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_tx_date ON credit_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

-- Response cache: stores LLM responses keyed by normalized question hash.
-- Two levels of matching:
--   Level 1: exact_hash   = SHA-256 of lowercase + stripped question
--   Level 2: normal_hash  = SHA-256 of stopword-removed + sorted tokens
-- Both levels match IT and EN questions independently.
CREATE TABLE IF NOT EXISTS response_cache (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    exact_hash      TEXT NOT NULL,
    normal_hash     TEXT NOT NULL,
    question        TEXT NOT NULL,
    generation      INTEGER NOT NULL,
    response        TEXT NOT NULL,
    hit_count       INTEGER NOT NULL DEFAULT 0,
    reviewed        INTEGER NOT NULL DEFAULT 0,   -- 0=auto, 1=human-reviewed
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_hit_at     TEXT DEFAULT NULL,
    reviewed_at     TEXT DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_cache_exact ON response_cache(exact_hash, generation);
CREATE INDEX IF NOT EXISTS idx_cache_normal ON response_cache(normal_hash, generation);

-- Custom stopwords added via admin panel.
-- Loaded at startup and merged with the built-in _STOPWORDS set
-- so the hash pipeline treats them the same way.
CREATE TABLE IF NOT EXISTS custom_stopwords (
    word       TEXT PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
