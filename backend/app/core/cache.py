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

    async def invalidate_all(self) -> int:
        """Clear the entire cache. Returns number of deleted entries."""
        cursor = await self._db.execute("SELECT COUNT(*) AS cnt FROM response_cache")
        row = await cursor.fetchone()
        count = row[0] if row else 0
        await self._db.execute("DELETE FROM response_cache")
        await self._db.commit()
        logger.info("Cache INVALIDATED: %d entries deleted", count)
        return count

    async def cleanup(self, max_age_days: int = 90) -> int:
        """Remove old entries that haven't been hit recently."""
        cursor = await self._db.execute(
            """DELETE FROM response_cache
               WHERE last_hit_at IS NULL AND created_at < datetime('now', ? || ' days')
                  OR last_hit_at < datetime('now', ? || ' days')""",
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
            "SELECT COUNT(*) AS total, COALESCE(SUM(hit_count), 0) AS hits FROM response_cache"
        )
        row = await cursor.fetchone()
        return {"total_entries": row[0], "total_hits": row[1]}

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
