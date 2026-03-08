"""Response cache with two-level hash matching (exact + normalized).

Level 1 — exact hash:
    lowercase + strip + collapse whitespace → SHA-256
    Catches identical questions with different casing/spacing.

Level 2 — normalized hash:
    lowercase + remove stopwords (IT/EN) + sort tokens → SHA-256
    Catches reworded questions like "debolezze garchomp gen 5"
    vs "gen 5 le debolezze di garchomp quali sono".

Both levels include the detected generation as a hard key,
so "debolezze Garchomp gen 5" never matches "debolezze Garchomp gen 8".
"""

import hashlib
import logging
import re

import aiosqlite

logger = logging.getLogger(__name__)

# ── Stopwords (IT + EN) — removed before normalized hash ────────────

_STOPWORDS: frozenset[str] = frozenset({
    # Italian
    "che", "chi", "per", "con", "del", "della", "delle", "dei", "degli",
    "nel", "nella", "nelle", "nei", "negli", "sul", "sulla", "sulle",
    "come", "cosa", "quali", "quale", "sono", "una", "uno", "gli", "non",
    "tra", "fra", "piu", "suo", "sua", "suoi", "sue", "questo", "questa",
    "quello", "quella", "molto", "poco", "troppo", "anche", "ancora",
    "parlami", "dimmi", "mostrami", "spiegami", "descrivi", "elenca",
    "confronta", "confronto", "vincerebbe", "scontro", "meglio",
    "impara", "apprende", "evolve", "hai", "puoi", "vorrei", "sapere",
    "pokemon", "pokémon", "tipo", "tipi", "mossa", "mosse",
    "abilita", "stat", "statistiche", "generazione", "gen",
    "debolezze", "debolezza", "resistenze", "resistenza", "immunita",
    "catena", "evolutiva", "evoluzione", "base", "totale",
    # English
    "what", "which", "who", "how", "does", "can", "the", "and",
    "are", "is", "of", "in", "for", "to", "from", "with", "has", "have",
    "its", "their", "this", "that", "about", "tell", "me", "show",
    "please", "pokemon", "type", "types", "move", "moves",
    "ability", "abilities", "stats", "statistics", "generation",
    "weakness", "weaknesses", "resistance", "resistances", "immunity",
    "evolution", "chain", "base", "total",
})


# ── Hash functions ──────────────────────────────────────────────────

def _exact_hash(question: str) -> str:
    """Level 1: lowercase + strip + collapse whitespace → SHA-256."""
    normalized = re.sub(r"\s+", " ", question.lower().strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _normal_hash(question: str) -> str:
    """Level 2: remove stopwords + sort remaining tokens → SHA-256."""
    tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", question.lower())
    filtered = sorted(t for t in tokens if t not in _STOPWORDS and len(t) >= 2)
    key = " ".join(filtered)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


# ── Cache class ─────────────────────────────────────────────────────

class ResponseCache:
    """Two-level response cache backed by SQLite."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    async def get(self, question: str, generation: int) -> str | None:
        """Look up a cached response. Returns response text or None.

        Tries exact hash first, then normalized hash. On hit, updates
        hit_count and last_hit_at for LRU tracking.
        """
        exact = _exact_hash(question)
        normal = _normal_hash(question)

        # Level 1: exact match
        row = await self._fetchone(
            "SELECT id, response FROM response_cache WHERE exact_hash = ? AND generation = ?",
            (exact, generation),
        )
        if row:
            await self._record_hit(row["id"])
            logger.info("Cache HIT (exact) for %r gen=%d", question[:60], generation)
            return row["response"]

        # Level 2: normalized match
        row = await self._fetchone(
            "SELECT id, response FROM response_cache WHERE normal_hash = ? AND generation = ?",
            (normal, generation),
        )
        if row:
            await self._record_hit(row["id"])
            logger.info("Cache HIT (normalized) for %r gen=%d", question[:60], generation)
            return row["response"]

        logger.info("Cache MISS for %r gen=%d", question[:60], generation)
        return None

    async def put(self, question: str, generation: int, response: str) -> None:
        """Store a response in the cache."""
        exact = _exact_hash(question)
        normal = _normal_hash(question)

        # Don't store duplicates (same exact_hash + generation)
        existing = await self._fetchone(
            "SELECT id FROM response_cache WHERE exact_hash = ? AND generation = ?",
            (exact, generation),
        )
        if existing:
            return

        await self._db.execute(
            """INSERT INTO response_cache
               (exact_hash, normal_hash, question, generation, response)
               VALUES (?, ?, ?, ?, ?)""",
            (exact, normal, question, generation, response),
        )
        await self._db.commit()
        logger.info("Cache STORE for %r gen=%d (%d chars)", question[:60], generation, len(response))

    async def invalidate_all(self, keep_reviewed: bool = True) -> int:
        """Clear the cache. Reviewed entries are preserved by default."""
        if keep_reviewed:
            cursor = await self._db.execute(
                "SELECT COUNT(*) AS cnt FROM response_cache WHERE reviewed = 0"
            )
            row = await cursor.fetchone()
            count = row[0] if row else 0
            await self._db.execute("DELETE FROM response_cache WHERE reviewed = 0")
        else:
            cursor = await self._db.execute(
                "SELECT COUNT(*) AS cnt FROM response_cache"
            )
            row = await cursor.fetchone()
            count = row[0] if row else 0
            await self._db.execute("DELETE FROM response_cache")
        await self._db.commit()
        logger.info("Cache INVALIDATED: %d entries deleted (keep_reviewed=%s)", count, keep_reviewed)
        return count

    async def cleanup(self, max_age_days: int = 90) -> int:
        """Remove old non-reviewed entries that haven't been hit recently."""
        cursor = await self._db.execute(
            """DELETE FROM response_cache
               WHERE reviewed = 0
                 AND (last_hit_at IS NULL AND created_at < datetime('now', ? || ' days')
                   OR last_hit_at < datetime('now', ? || ' days'))""",
            (f"-{max_age_days}", f"-{max_age_days}"),
        )
        await self._db.commit()
        deleted = cursor.rowcount
        if deleted:
            logger.info("Cache CLEANUP: %d stale entries removed", deleted)
        return deleted

    async def stats(self) -> dict:
        """Return cache statistics."""
        cursor = await self._db.execute(
            """SELECT
                 COUNT(*) AS total,
                 COALESCE(SUM(hit_count), 0) AS hits,
                 SUM(CASE WHEN reviewed = 1 THEN 1 ELSE 0 END) AS reviewed_count
               FROM response_cache"""
        )
        row = await cursor.fetchone()
        return {
            "total_entries": row[0],
            "total_hits": row[1],
            "reviewed_entries": row[2],
        }

    # ── List & Edit (admin review) ───────────────────────────────────

    async def list_entries(
        self,
        page: int = 1,
        per_page: int = 20,
        reviewed_only: bool | None = None,
        generation: int | None = None,
        search: str | None = None,
    ) -> dict:
        """List cache entries with pagination and optional filters."""
        conditions: list[str] = []
        params: list = []

        if reviewed_only is True:
            conditions.append("reviewed = 1")
        elif reviewed_only is False:
            conditions.append("reviewed = 0")

        if generation is not None:
            conditions.append("generation = ?")
            params.append(generation)

        if search:
            conditions.append("question LIKE ?")
            params.append(f"%{search}%")

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Total count
        cursor = await self._db.execute(
            f"SELECT COUNT(*) FROM response_cache {where}", params,
        )
        row = await cursor.fetchone()
        total = row[0]

        # Paginated results
        offset = (page - 1) * per_page
        cursor = await self._db.execute(
            f"""SELECT id, question, generation, response, hit_count,
                       reviewed, created_at, last_hit_at, reviewed_at
                FROM response_cache {where}
                ORDER BY hit_count DESC, created_at DESC
                LIMIT ? OFFSET ?""",
            [*params, per_page, offset],
        )
        rows = await cursor.fetchall()

        entries = [
            {
                "id": r[0],
                "question": r[1],
                "generation": r[2],
                "response": r[3],
                "hit_count": r[4],
                "reviewed": bool(r[5]),
                "created_at": r[6],
                "last_hit_at": r[7],
                "reviewed_at": r[8],
            }
            for r in rows
        ]

        return {
            "entries": entries,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if total else 0,
        }

    async def update_entry(self, entry_id: int, response: str) -> dict | None:
        """Update a cache entry's response and mark it as reviewed."""
        row = await self._fetchone(
            "SELECT id FROM response_cache WHERE id = ?", (entry_id,),
        )
        if not row:
            return None

        await self._db.execute(
            """UPDATE response_cache
               SET response = ?, reviewed = 1, reviewed_at = datetime('now')
               WHERE id = ?""",
            (response, entry_id),
        )
        await self._db.commit()
        logger.info("Cache entry #%d REVIEWED and updated", entry_id)

        cursor = await self._db.execute(
            """SELECT id, question, generation, response, hit_count,
                      reviewed, created_at, last_hit_at, reviewed_at
               FROM response_cache WHERE id = ?""",
            (entry_id,),
        )
        r = await cursor.fetchone()
        return {
            "id": r[0],
            "question": r[1],
            "generation": r[2],
            "response": r[3],
            "hit_count": r[4],
            "reviewed": bool(r[5]),
            "created_at": r[6],
            "last_hit_at": r[7],
            "reviewed_at": r[8],
        }

    async def mark_reviewed(self, entry_id: int) -> bool:
        """Mark an entry as reviewed without changing the response."""
        row = await self._fetchone(
            "SELECT id FROM response_cache WHERE id = ?", (entry_id,),
        )
        if not row:
            return False

        await self._db.execute(
            """UPDATE response_cache
               SET reviewed = 1, reviewed_at = datetime('now')
               WHERE id = ?""",
            (entry_id,),
        )
        await self._db.commit()
        logger.info("Cache entry #%d marked as REVIEWED", entry_id)
        return True

    # ── Internal ────────────────────────────────────────────────────

    async def _record_hit(self, entry_id: int) -> None:
        await self._db.execute(
            "UPDATE response_cache SET hit_count = hit_count + 1, last_hit_at = datetime('now') WHERE id = ?",
            (entry_id,),
        )
        await self._db.commit()

    async def _fetchone(self, sql: str, params: tuple = ()):
        cursor = await self._db.execute(sql, params)
        return await cursor.fetchone()
