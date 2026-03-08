"""Response cache with two-level hash matching (exact + normalized).

Level 1 — exact hash:
    lowercase + strip + collapse whitespace → SHA-256
    Catches identical questions with different casing/spacing.

Level 2 — normalized hash:
    1. Lowercase + tokenize
    2. Convert ordinals to digits (quinta → 5, fifth → 5)
    3. Normalize plurals to singular (debolezze → debolezza)
    4. Strip generation references (gen keyword + adjacent number)
       since generation is already a separate DB column
    5. Remove generic stopwords (articles, prepositions, pronouns)
       but KEEP semantically important Pokemon terms (debolezza,
       mossa, tipo, etc.) to avoid false positives
    6. Sort remaining tokens → SHA-256

Both levels include the detected generation as a hard key,
so "debolezze Garchomp gen 5" never matches "debolezze Garchomp gen 8".
"""

import hashlib
import logging
import re

import aiosqlite

logger = logging.getLogger(__name__)

# ── Stopwords — ONLY generic words, NOT Pokemon-specific terms ──────
# Pokemon terms (debolezza, mossa, tipo, abilita, etc.) are
# semantically important and MUST stay in the hash to prevent
# false positives (e.g. "mosse garchomp" ≠ "debolezze garchomp").

_STOPWORDS: frozenset[str] = frozenset({
    # Italian — articles, prepositions, pronouns, conjunctions
    "il", "lo", "la", "le", "li", "un", "una", "uno", "gli", "dei",
    "del", "della", "delle", "degli", "nel", "nella", "nelle", "nei",
    "negli", "sul", "sulla", "sulle", "al", "alla", "alle", "ai",
    "che", "chi", "per", "con", "tra", "fra", "non", "piu", "di",
    "come", "cosa", "quali", "quale", "sono", "suo", "sua", "suoi",
    "sue", "questo", "questa", "quello", "quella",
    "molto", "poco", "troppo", "anche", "ancora",
    # Italian — common verbs in questions
    "ha", "hai", "puoi", "può", "fa", "vai", "vorrei", "sapere",
    "parlami", "dimmi", "mostrami", "spiegami", "descrivi", "elenca",
    "confronta", "confronto", "vincerebbe", "scontro", "meglio",
    # Italian — only truly generic Pokemon word
    "pokemon", "pokémon",
    # Generation keywords (number is stripped separately)
    "gen", "generazione", "generation",
    # English — articles, prepositions, pronouns, conjunctions
    "what", "which", "who", "how", "does", "can", "the", "and",
    "are", "is", "of", "in", "for", "to", "from", "with", "has", "have",
    "its", "their", "this", "that", "about", "tell", "me", "show",
    "please", "pokemon",
})

# ── Ordinal → digit conversion (IT + EN) ────────────────────────────

_ORDINAL_MAP: dict[str, str] = {
    # Italian (masc + fem)
    "prima": "1", "primo": "1",
    "seconda": "2", "secondo": "2",
    "terza": "3", "terzo": "3",
    "quarta": "4", "quarto": "4",
    "quinta": "5", "quinto": "5",
    "sesta": "6", "sesto": "6",
    "settima": "7", "settimo": "7",
    "ottava": "8", "ottavo": "8",
    "nona": "9", "nono": "9",
    # English (words + abbreviated)
    "first": "1", "1st": "1",
    "second": "2", "2nd": "2",
    "third": "3", "3rd": "3",
    "fourth": "4", "4th": "4",
    "fifth": "5", "5th": "5",
    "sixth": "6", "6th": "6",
    "seventh": "7", "7th": "7",
    "eighth": "8", "8th": "8",
    "ninth": "9", "9th": "9",
}

# ── Plural → singular normalization (IT + EN) ───────────────────────
# Only Pokemon-relevant terms that could appear as both forms.

_PLURAL_MAP: dict[str, str] = {
    # Italian
    "debolezze": "debolezza",
    "resistenze": "resistenza",
    "mosse": "mossa",
    "statistiche": "statistica",
    "tipi": "tipo",
    "evoluzioni": "evoluzione",
    # English
    "weaknesses": "weakness",
    "resistances": "resistance",
    "moves": "move",
    "types": "type",
    "abilities": "ability",
    "stats": "stat",
    "evolutions": "evolution",
}

# ── Generation keyword triggers ─────────────────────────────────────
# When one of these appears adjacent to a number, the number is
# stripped from the hash (generation is a separate DB column).

_GEN_KEYWORDS = frozenset({"gen", "generazione", "generation"})


# ── Hash functions ──────────────────────────────────────────────────

def _exact_hash(question: str) -> str:
    """Level 1: lowercase + strip + collapse whitespace → SHA-256."""
    normalized = re.sub(r"\s+", " ", question.lower().strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _split_gen_tokens(tokens: list[str]) -> list[str]:
    """Split aggregated generation tokens: gen4 → gen + 4, generation5 → generation + 5."""
    result: list[str] = []
    for t in tokens:
        m = re.match(r"^(gen|generazione|generation)(\d)$", t)
        if m:
            result.append(m.group(1))
            result.append(m.group(2))
        else:
            result.append(t)
    return result


def _normal_hash(question: str) -> str:
    """Level 2: normalize + strip gen refs + remove stopwords + sort → SHA-256."""
    tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", question.lower())

    # Step 0: split aggregated gen tokens (gen4 → gen + 4)
    tokens = _split_gen_tokens(tokens)

    # Step 1: ordinals → digits  (quinta → 5, fifth → 5)
    tokens = [_ORDINAL_MAP.get(t, t) for t in tokens]

    # Step 2: plurals → singulars (debolezze → debolezza)
    tokens = [_PLURAL_MAP.get(t, t) for t in tokens]

    # Step 3: find generation-adjacent numbers and mark for removal.
    # Generation is already stored as a separate column, so the
    # number in the question (e.g. "gen 5", "quinta generazione")
    # must NOT appear in the hash.
    gen_number_indices: set[int] = set()
    for i, t in enumerate(tokens):
        if t in _GEN_KEYWORDS:
            if i > 0 and tokens[i - 1].isdigit():
                gen_number_indices.add(i - 1)
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                gen_number_indices.add(i + 1)

    # Step 4: filter stopwords, short tokens, gen-adjacent numbers
    filtered = sorted(
        t for i, t in enumerate(tokens)
        if t not in _STOPWORDS
        and len(t) >= 2
        and i not in gen_number_indices
    )

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
                       reviewed, created_at, last_hit_at, reviewed_at,
                       exact_hash, normal_hash
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
                "exact_hash": r[9][:12] + "…",
                "normal_hash": r[10][:12] + "…",
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

    # ── Export ────────────────────────────────────────────────────

    async def export_all(self) -> list[dict]:
        """Export all cache entries as a list of dicts (for CSV export)."""
        cursor = await self._db.execute(
            """SELECT id, question, generation, response, hit_count,
                      reviewed, exact_hash, normal_hash,
                      created_at, last_hit_at, reviewed_at
               FROM response_cache
               ORDER BY id"""
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "question": r[1],
                "generation": r[2],
                "response": r[3],
                "hit_count": r[4],
                "reviewed": r[5],
                "exact_hash": r[6],
                "normal_hash": r[7],
                "created_at": r[8],
                "last_hit_at": r[9],
                "reviewed_at": r[10],
            }
            for r in rows
        ]

    # ── Debug ─────────────────────────────────────────────────────

    @staticmethod
    def debug_hash(question: str, generation: int) -> dict:
        """Show how a question would be hashed (no DB interaction).

        Returns the exact hash, normal hash, and the intermediate
        normalized tokens so you can verify the pipeline visually.
        """
        tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", question.lower())

        # Step 0: split gen tokens
        tokens = _split_gen_tokens(tokens)
        after_split = list(tokens)

        # Step 1: ordinals
        tokens = [_ORDINAL_MAP.get(t, t) for t in tokens]
        after_ordinals = list(tokens)

        # Step 2: plurals
        tokens = [_PLURAL_MAP.get(t, t) for t in tokens]
        after_plurals = list(tokens)

        # Step 3: gen numbers
        gen_number_indices: set[int] = set()
        for i, t in enumerate(tokens):
            if t in _GEN_KEYWORDS:
                if i > 0 and tokens[i - 1].isdigit():
                    gen_number_indices.add(i - 1)
                if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                    gen_number_indices.add(i + 1)

        # Step 4: filter
        filtered = sorted(
            t for i, t in enumerate(tokens)
            if t not in _STOPWORDS
            and len(t) >= 2
            and i not in gen_number_indices
        )

        return {
            "question": question,
            "generation": generation,
            "exact_hash": _exact_hash(question)[:16],
            "normal_hash": _normal_hash(question)[:16],
            "pipeline": {
                "0_after_gen_split": after_split,
                "1_after_ordinals": after_ordinals,
                "2_after_plurals": after_plurals,
                "3_gen_numbers_removed": sorted(gen_number_indices),
                "4_final_tokens": filtered,
                "5_hash_input": " ".join(filtered),
            },
        }

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
