"""Async SQLite database for user and credit management."""

import uuid
from pathlib import Path

import aiosqlite


class Database:
    """Thin async wrapper around SQLite for users and credits."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    # --- Lifecycle ---

    async def connect(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._init_schema()

    async def _init_schema(self) -> None:
        schema_path = Path(__file__).parent / "schema.sql"
        schema_sql = schema_path.read_text(encoding="utf-8")
        await self._conn.executescript(schema_sql)

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    # --- Users ---

    async def upsert_user(
        self,
        google_id: str,
        email: str,
        name: str,
        picture_url: str,
    ) -> dict:
        """Create or update a user by Google ID. Returns user dict."""
        row = await self._fetchone(
            "SELECT * FROM users WHERE google_id = ?", (google_id,)
        )
        if row:
            await self._conn.execute(
                """UPDATE users
                   SET email = ?, name = ?, picture_url = ?,
                       updated_at = datetime('now')
                   WHERE google_id = ?""",
                (email, name, picture_url, google_id),
            )
            await self._conn.commit()
            row = await self._fetchone(
                "SELECT * FROM users WHERE google_id = ?", (google_id,)
            )
        else:
            user_id = str(uuid.uuid4())
            await self._conn.execute(
                """INSERT INTO users (id, google_id, email, name, picture_url)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, google_id, email, name, picture_url),
            )
            await self._conn.commit()
            row = await self._fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
        return dict(row)

    async def get_user_by_id(self, user_id: str) -> dict | None:
        row = await self._fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
        return dict(row) if row else None

    # --- Credits ---

    async def get_credit_balance(
        self, user_id: str, daily_free_limit: int
    ) -> dict:
        """Calculate current credit balance for a user.

        Daily free credits reset automatically at midnight because we
        only count today's ``daily_free_deduction`` rows.
        """
        row = await self._fetchone(
            """SELECT COUNT(*) AS cnt FROM credit_transactions
               WHERE user_id = ? AND type = 'daily_free_deduction'
                 AND date(created_at) = date('now')""",
            (user_id,),
        )
        today_free_used = row["cnt"] if row else 0
        daily_free_remaining = max(0, daily_free_limit - today_free_used)

        user = await self._fetchone(
            "SELECT paid_credits FROM users WHERE id = ?", (user_id,)
        )
        paid = user["paid_credits"] if user else 0

        return {
            "daily_free_remaining": daily_free_remaining,
            "daily_free_total": daily_free_limit,
            "paid_credits": paid,
            "total_available": daily_free_remaining + paid,
        }

    async def record_deduction(self, user_id: str, deduction_type: str) -> None:
        """Record a credit deduction (1 credit).

        ``deduction_type`` must be ``'daily_free_deduction'`` or
        ``'paid_deduction'``.
        """
        if deduction_type == "paid_deduction":
            await self._conn.execute(
                "UPDATE users SET paid_credits = paid_credits - 1 WHERE id = ?",
                (user_id,),
            )

        # Fetch current balance for snapshot
        user = await self._fetchone(
            "SELECT paid_credits FROM users WHERE id = ?", (user_id,)
        )
        balance = user["paid_credits"] if user else 0

        await self._conn.execute(
            """INSERT INTO credit_transactions
               (user_id, amount, type, balance_after)
               VALUES (?, -1, ?, ?)""",
            (user_id, deduction_type, balance),
        )
        await self._conn.commit()

    async def add_purchased_credits(
        self,
        user_id: str,
        amount: int,
        stripe_session_id: str,
    ) -> None:
        """Add purchased credits (idempotent via stripe_session_id)."""
        existing = await self._fetchone(
            "SELECT id FROM credit_transactions WHERE stripe_session_id = ?",
            (stripe_session_id,),
        )
        if existing:
            return  # Already processed

        await self._conn.execute(
            "UPDATE users SET paid_credits = paid_credits + ? WHERE id = ?",
            (amount, user_id),
        )
        user = await self._fetchone(
            "SELECT paid_credits FROM users WHERE id = ?", (user_id,)
        )
        balance = user["paid_credits"] if user else 0

        await self._conn.execute(
            """INSERT INTO credit_transactions
               (user_id, amount, type, balance_after, stripe_session_id)
               VALUES (?, ?, 'purchase', ?, ?)""",
            (user_id, amount, balance, stripe_session_id),
        )
        await self._conn.commit()

    # --- Internal helpers ---

    async def _fetchone(self, sql: str, params: tuple = ()) -> aiosqlite.Row | None:
        cursor = await self._conn.execute(sql, params)
        return await cursor.fetchone()
