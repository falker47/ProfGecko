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
