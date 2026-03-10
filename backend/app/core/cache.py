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
       AND game title words (platino, nero, diamond, sword, etc.)
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

# ── Custom stopwords (loaded from DB at startup, managed via admin) ──
# This set is merged with _STOPWORDS in the hash pipeline.
# Use load_custom_stopwords() to populate from the DB.
_custom_stopwords: set[str] = set()

# ── Stopwords — ONLY generic words, NOT Pokemon-specific terms ──────
# Pokemon terms (debolezza, mossa, tipo, abilita, etc.) are
# semantically important and MUST stay in the hash to prevent
# false positives (e.g. "mosse garchomp" ≠ "debolezze garchomp").

_STOPWORDS: frozenset[str] = frozenset({
    # Italian — articles, prepositions, pronouns, conjunctions
    "il", "lo", "la", "le", "li", "un", "una", "uno", "gli", "dei", "dammi",
    "del", "della", "delle", "degli", "dettagli", "nel", "nella", "nelle", "nei",
    "negli", "sul", "sulla", "sulle", "al", "alla", "alle", "ai",
    "che", "chi", "per", "con", "tra", "fra", "non", "piu", "più", "di", "mi",
    "come", "cosa", "quali", "quale", "qual", "si", "sono", "suo", "sua",
    "suoi", "sue", "questo", "questa", "quello", "quella", "questi",
    "queste", "quanti", "quante", "quanto",
    "tutto", "tutta", "tutti", "tutte",
    "molto", "poco", "troppo", "anche", "ancora", "tanto", "così", "cosi",
    "su", "nei", "oppure",
    "perché", "perche", "perchè",  # interrogative / conjunction
    # Italian — common verbs / filler in questions
    "ha", "hai", "puoi", "può", "fa", "vai", "vorrei", "sapere",
    "parlami", "dimmi", "mostrami", "spiegami", "descrivi", "elenca",
    "confronta", "confronto", "vincerebbe", "scontro",
    "funziona", "funzionano", "impara", "apprende", "possiede",
    "affrontare", "avventura",
    "cos",  # from "cos'è" (tokenized as "cos" + "è")
    # NOTE: parole strategiche (consiglio, meglio, conviene, etc.) e
    # trainer (capipalestra, superquattro, etc.) NON sono stopwords.
    # Vengono normalizzate a token canonici in _STRATEGIC_SYNONYM_MAP
    # per distinguere query esplorative da query strategiche.
    # Italian — generic adjectives / nouns in questions
    "forte", "buono", "buona", "bene", "male",
    "info", "informazioni", "effetto",
    "base", "punti", "catena",  # "stat base", "punti deboli", "catena evolutiva"
    "vs",  # "Garchomp vs Salamence"
    # Italian — only truly generic Pokemon word
    "pokemon", "pokémon",
    # Generation keywords (number is stripped separately)
    "gen", "generazione", "generation",
    # English — articles, prepositions, pronouns, conjunctions
    "what", "which", "who", "how", "does", "can", "the", "and",
    "are", "is", "of", "in", "for", "to", "from", "with", "has", "have",
    "its", "their", "this", "that", "about", "tell", "me", "show",
    "please", "pokemon", "learn", "learns",
    "effect", "info", "strong", "good", "vs", "details",
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

# ── Synonym / plural normalization (IT + EN) ─────────────────────────
# Maps variant forms to a canonical token so different phrasings
# produce the same hash (e.g. "debole" → "debolezza",
# "catena evolutiva" → "evoluzione", "stat" → "statistica").

_PLURAL_MAP: dict[str, str] = {
    # Italian — plurals
    "debolezze": "debolezza",
    "resistenze": "resistenza",
    "mosse": "mossa",
    "statistiche": "statistica",
    "tipi": "tipo",
    "evoluzioni": "evoluzione",
    # Italian — adjective/verb → noun synonyms
    "debole": "debolezza",
    "deboli": "debolezza",
    "vulnerabile": "debolezza",
    "resistente": "resistenza",
    "evolve": "evoluzione",
    "evolutiva": "evoluzione",
    "evolutivo": "evoluzione",
    # Italian — abbreviations
    "stat": "statistica",
    "stats": "statistica",
    # English — plurals
    "weaknesses": "weakness",
    "resistances": "resistance",
    "moves": "move",
    "types": "type",
    "abilities": "ability",
    # English — synonyms (evolution terms → IT canonical "evoluzione")
    "evolution": "evoluzione",
    "evolutions": "evoluzione",
    "evolves": "evoluzione",
    "weak": "weakness",
    "moveset": "move",
}

# ── Strategic intent normalization ────────────────────────────────
# Tutte le parole che indicano "consiglio strategico" convergono
# al token canonico _consiglio_. Questo distingue query esplorative
# ("quali starter ci sono") da query strategiche ("miglior starter").
# Analogamente, termini relativi a trainer/palestre convergono a
# _trainer_ per evitare hash vuoti e distinguere il contesto.

_STRATEGIC_SYNONYM_MAP: dict[str, str] = {
    # IT — advisory intent → _consiglio_
    "consiglio": "_consiglio_",
    "consigli": "_consiglio_",
    "consigliata": "_consiglio_",
    "consigliato": "_consiglio_",
    "consiglia": "_consiglio_",
    "consigliami": "_consiglio_",
    "migliore": "_consiglio_",
    "migliori": "_consiglio_",
    "miglior": "_consiglio_",
    "meglio": "_consiglio_",
    "conviene": "_consiglio_",
    "scegliere": "_consiglio_",
    # EN — advisory intent → _consiglio_
    "best": "_consiglio_",
    "recommend": "_consiglio_",
    "recommended": "_consiglio_",
    "should": "_consiglio_",
    # IT — trainer / gym terms → _trainer_
    "capopalestra": "_trainer_",
    "capipalestra": "_trainer_",
    "superquattro": "_trainer_",
    "campione": "_trainer_",
    "palestra": "_trainer_",
    "palestre": "_trainer_",
    "lega": "_trainer_",
    # EN — trainer terms → _trainer_
    "gym": "_trainer_",
    "leader": "_trainer_",
    "champion": "_trainer_",
    "gymleader": "_trainer_",
    "league": "_trainer_",
    "elitefour": "_trainer_",
}

# ── Generation keyword triggers ─────────────────────────────────────
# When one of these appears adjacent to a number, the number is
# stripped from the hash (generation is a separate DB column).

_GEN_KEYWORDS = frozenset({"gen", "generazione", "generation"})

# ── Game title stopwords ──────────────────────────────────────────
# Game titles are stripped because the generation is already stored
# as a separate DB column. This way "garchomp debolezze platino"
# matches "garchomp debolezze gen 4" (both → gen=4, hash=same tokens).
# Excluded from this set: words that overlap with Pokemon type/move
# terms (fuoco, fire, leaf, green) — these are handled conditionally
# via _CONDITIONAL_GAME_TOKENS below.
# Also excluded: pikachu/eevee/arceus (Pokemon names in game titles).

_GAME_TITLE_STOPWORDS: frozenset[str] = frozenset({
    # NOTE: all entries MUST be lowercase — tokens are lowercased before matching.
    # Gen 1
    "rosso", "blu", "giallo", "red", "blue", "yellow",
    "rb",
    # Gen 2
    "oro", "argento", "cristallo", "gold", "silver", "crystal",
    "gs",
    # Gen 3
    "rubino", "zaffiro", "smeraldo", "ruby", "sapphire", "emerald",
    "rossofuoco", "verdefoglia", "firered", "leafgreen",
    "frlg", "rse", "rs", "fr", "lg",
    # Gen 4
    "diamante", "perla", "platino", "diamond", "pearl", "platinum",
    "heartgold", "soulsilver",
    "dp", "pt", "hgss",
    # Gen 5
    "nero", "bianco", "nero2", "bianco2", "black", "white", "black2", "white2",
    "bw", "bw2",
    # Gen 6
    "omega", "alpha",
    "oras", "xy",
    # Gen 7
    "sole", "luna", "ultrasole", "ultraluna", "sun", "moon", "ultrasun", "ultramoon",
    "usum", "sm",
    # Gen 8
    "spada", "scudo", "sword", "shield",
    "swsh", "bdsp",
    "lucente", "splendente", "brilliant", "shining",
    "leggende", "legends",
    # Gen 9
    "scarlatto", "violetto", "scarlet", "violet", "sv",
})

# ── Conditional game title tokens ─────────────────────────────────
# Words that are part of a game title BUT also have independent
# Pokemon meaning (type/move terms). They are stripped only when
# adjacent to their companion word from the game title.
# E.g. "fuoco" stays in "tipo fuoco" but is stripped in "rosso fuoco".

_CONDITIONAL_GAME_TOKENS: dict[str, frozenset[str]] = {
    # "rosso fuoco" / "verde foglia" (IT gen 3)
    "fuoco": frozenset({"rosso"}),
    # "fire red" / "leaf green" (EN gen 3)
    "fire": frozenset({"red"}),
    "leaf": frozenset({"green"}),
    "green": frozenset({"leaf"}),
}


def _find_conditional_indices(tokens: list[str]) -> set[int]:
    """Find token indices that should be stripped conditionally.

    A token is stripped only when adjacent to its companion word
    from a multi-word game title (e.g. "fuoco" next to "rosso").
    """
    indices: set[int] = set()
    for i, t in enumerate(tokens):
        triggers = _CONDITIONAL_GAME_TOKENS.get(t)
        if triggers:
            prev_match = i > 0 and tokens[i - 1] in triggers
            next_match = i + 1 < len(tokens) and tokens[i + 1] in triggers
            if prev_match or next_match:
                indices.add(i)
    return indices


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


def _compute_final_tokens(question: str) -> list[str]:
    """Compute the normalized, sorted, deduplicated tokens for a question.

    This is the core normalization logic shared by _normal_hash and
    the duplicate-groups endpoint. Returns the list of tokens that
    form the hash input.
    """
    tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", question.lower())

    # Step 0: split aggregated gen tokens (gen4 → gen + 4)
    tokens = _split_gen_tokens(tokens)

    # Step 1: ordinals → digits  (quinta → 5, fifth → 5)
    tokens = [_ORDINAL_MAP.get(t, t) for t in tokens]

    # Step 2a: plurals → singulars (debolezze → debolezza)
    tokens = [_PLURAL_MAP.get(t, t) for t in tokens]

    # Step 2b: strategic intent normalization
    # (consiglio/migliore/meglio → _consiglio_, capipalestra → _trainer_)
    tokens = [_STRATEGIC_SYNONYM_MAP.get(t, t) for t in tokens]

    # Step 3: find generation-adjacent numbers and mark for removal.
    gen_number_indices: set[int] = set()
    for i, t in enumerate(tokens):
        if t in _GEN_KEYWORDS:
            if i > 0 and tokens[i - 1].isdigit():
                gen_number_indices.add(i - 1)
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                gen_number_indices.add(i + 1)

    # Step 3c: conditional game title tokens
    conditional_indices = _find_conditional_indices(tokens)

    # Step 4: filter and deduplicate
    all_stopwords = _STOPWORDS | _custom_stopwords
    return sorted(set(
        t for i, t in enumerate(tokens)
        if t not in all_stopwords
        and t not in _GAME_TITLE_STOPWORDS
        and len(t) >= 2
        and i not in gen_number_indices
        and i not in conditional_indices
    ))


def _normal_hash(question: str) -> str:
    """Level 2: normalize + strip gen refs + remove stopwords + sort → SHA-256."""
    filtered = _compute_final_tokens(question)
    key = " ".join(filtered)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


# ── Custom stopwords I/O ──────────────────────────────────────────

async def load_custom_stopwords(db: aiosqlite.Connection) -> int:
    """Load custom stopwords from DB into the module-level set.

    Call once at startup. Returns the number of words loaded.
    """
    global _custom_stopwords
    cursor = await db.execute("SELECT word FROM custom_stopwords")
    rows = await cursor.fetchall()
    _custom_stopwords = {r[0] for r in rows}
    if _custom_stopwords:
        logger.info("Loaded %d custom stopwords: %s",
                     len(_custom_stopwords), sorted(_custom_stopwords))
    return len(_custom_stopwords)


# ── Cache class ─────────────────────────────────────────────────────

class ResponseCache:
    """Two-level response cache backed by SQLite."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    # ── Custom stopwords management ──────────────────────────────

    async def list_stopwords(self) -> list[str]:
        """Return all custom stopwords sorted alphabetically."""
        cursor = await self._db.execute(
            "SELECT word FROM custom_stopwords ORDER BY word"
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]

    async def add_stopwords(self, words: list[str]) -> dict:
        """Add one or more custom stopwords. Updates the in-memory set too."""
        global _custom_stopwords
        added = 0
        for w in words:
            w = w.lower().strip()
            if not w or len(w) < 2:
                continue
            try:
                await self._db.execute(
                    "INSERT OR IGNORE INTO custom_stopwords (word) VALUES (?)",
                    (w,),
                )
                _custom_stopwords.add(w)
                added += 1
            except Exception:
                pass
        await self._db.commit()
        logger.info("Custom stopwords ADD: %d words added, total now %d",
                     added, len(_custom_stopwords))
        return {"added": added, "total": len(_custom_stopwords)}

    async def remove_stopword(self, word: str) -> bool:
        """Remove a custom stopword."""
        global _custom_stopwords
        word = word.lower().strip()
        cursor = await self._db.execute(
            "DELETE FROM custom_stopwords WHERE word = ?", (word,),
        )
        await self._db.commit()
        _custom_stopwords.discard(word)
        removed = cursor.rowcount > 0
        if removed:
            logger.info("Custom stopword REMOVED: %r", word)
        return removed

    async def get(self, question: str, generation: int) -> tuple[str, int] | None:
        """Look up a cached response.

        Returns (response_text, entry_id) on hit, or None on miss.
        Tries exact hash first, then normalized hash. On hit, updates
        hit_count and last_hit_at for LRU tracking.

        Skips entries with feedback='M' (auto-detected "missing info"
        responses) so they get re-generated with the current prompt.
        Only reviewed entries ('Y') and unreviewed ('-') are served.
        """
        exact = _exact_hash(question)
        normal = _normal_hash(question)

        # Level 1: exact match
        row = await self._fetchone(
            "SELECT id, response, feedback FROM response_cache WHERE exact_hash = ? AND generation = ?",
            (exact, generation),
        )
        if row:
            if row["feedback"] == "M":
                logger.info("Cache SKIP (exact, feedback=M) for %r gen=%d", question[:60], generation)
            else:
                await self._record_hit(row["id"])
                logger.info("Cache HIT (exact) for %r gen=%d", question[:60], generation)
                return (row["response"], row["id"])

        # Level 2: normalized match
        row = await self._fetchone(
            "SELECT id, response, feedback FROM response_cache WHERE normal_hash = ? AND generation = ?",
            (normal, generation),
        )
        if row:
            if row["feedback"] == "M":
                logger.info("Cache SKIP (normalized, feedback=M) for %r gen=%d", question[:60], generation)
            else:
                await self._record_hit(row["id"])
                logger.info("Cache HIT (normalized) for %r gen=%d", question[:60], generation)
                return (row["response"], row["id"])

        logger.info("Cache MISS for %r gen=%d", question[:60], generation)
        return None

    async def put(
        self,
        question: str,
        generation: int,
        response: str,
        feedback: str = "-",
    ) -> int | None:
        """Store a response in the cache. Returns the entry ID, or None if duplicate."""
        exact = _exact_hash(question)
        normal = _normal_hash(question)

        # Don't store duplicates (same exact_hash + generation).
        # Exception: if the existing entry is feedback='M' (auto-detected
        # missing) and the new response is NOT missing, replace it — the
        # improved prompt may have resolved the issue.
        existing = await self._fetchone(
            "SELECT id, feedback FROM response_cache WHERE exact_hash = ? AND generation = ?",
            (exact, generation),
        )
        if existing:
            if existing["feedback"] == "M" and feedback != "M":
                # Replace stale "missing info" entry with new good response
                await self._db.execute(
                    """UPDATE response_cache
                       SET response = ?, feedback = ?, normal_hash = ?,
                           hit_count = 0, last_hit_at = NULL
                       WHERE id = ?""",
                    (response, feedback, normal, existing["id"]),
                )
                await self._db.commit()
                logger.info("Cache REPLACE (M→%s) for %r gen=%d", feedback, question[:60], generation)
                return existing["id"]
            return existing["id"]

        cursor = await self._db.execute(
            """INSERT INTO response_cache
               (exact_hash, normal_hash, question, generation, response, feedback)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (exact, normal, question, generation, response, feedback),
        )
        await self._db.commit()
        logger.info("Cache STORE for %r gen=%d (%d chars) feedback=%s",
                     question[:60], generation, len(response), feedback)
        return cursor.lastrowid

    async def set_feedback(self, entry_id: int, feedback: str) -> bool:
        """Set user feedback on a cache entry. Only V (correct) or F (wrong) allowed."""
        if feedback not in ("V", "F"):
            return False
        cursor = await self._db.execute(
            "UPDATE response_cache SET feedback = ? WHERE id = ?",
            (feedback, entry_id),
        )
        await self._db.commit()
        if cursor.rowcount > 0:
            logger.info("Cache entry #%d feedback set to %s", entry_id, feedback)
        return cursor.rowcount > 0

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

    # Colonne ammesse per l'ordinamento (whitelist anti-SQL-injection)
    _SORT_COLUMNS = {"id", "generation", "created_at", "hit_count"}

    async def list_entries(
        self,
        page: int = 1,
        per_page: int = 20,
        reviewed_only: bool | None = None,
        generation: int | None = None,
        search: str | None = None,
        feedback: str | None = None,
        sort_by: str = "id",
        sort_order: str = "desc",
    ) -> dict:
        """List cache entries with pagination, filters and sorting."""
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

        if feedback is not None and feedback in ("V", "F", "M", "-"):
            conditions.append("feedback = ?")
            params.append(feedback)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Sanitize sort parameters
        col = sort_by if sort_by in self._SORT_COLUMNS else "id"
        direction = "ASC" if sort_order.lower() == "asc" else "DESC"

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
                       exact_hash, normal_hash, feedback
                FROM response_cache {where}
                ORDER BY {col} {direction}
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
                "feedback": r[11],
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

    async def update_entry(
        self,
        entry_id: int,
        response: str | None = None,
        generation: int | None = None,
    ) -> dict | None:
        """Update a cache entry's response and/or generation, mark as reviewed.

        If generation changes, hashes are recomputed automatically.
        """
        row = await self._fetchone(
            "SELECT id, question FROM response_cache WHERE id = ?", (entry_id,),
        )
        if not row:
            return None

        sets: list[str] = ["reviewed = 1", "reviewed_at = datetime('now')"]
        params: list = []

        if response is not None:
            sets.append("response = ?")
            params.append(response)

        if generation is not None:
            # Recompute hashes for the new generation context
            question = row[1]
            sets.append("generation = ?")
            params.append(generation)
            sets.append("exact_hash = ?")
            params.append(_exact_hash(question))
            sets.append("normal_hash = ?")
            params.append(_normal_hash(question))

        params.append(entry_id)
        await self._db.execute(
            f"UPDATE response_cache SET {', '.join(sets)} WHERE id = ?",
            tuple(params),
        )
        await self._db.commit()
        logger.info("Cache entry #%d UPDATED (response=%s, gen=%s)",
                     entry_id, response is not None, generation)

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

    async def delete_entry(self, entry_id: int) -> bool:
        """Delete a single cache entry by ID."""
        row = await self._fetchone(
            "SELECT id FROM response_cache WHERE id = ?", (entry_id,),
        )
        if not row:
            return False

        await self._db.execute(
            "DELETE FROM response_cache WHERE id = ?", (entry_id,),
        )
        await self._db.commit()
        logger.info("Cache entry #%d DELETED", entry_id)
        return True

    # ── Import (bulk seed) ─────────────────────────────────────────

    async def import_entries(
        self,
        rows: list[dict],
        skip_duplicates: bool = True,
    ) -> dict:
        """Bulk-import cache entries from a list of dicts.

        Each dict must have: question, generation, response.
        Hashes are computed automatically. Entries are stored as reviewed=0.
        If skip_duplicates is True, entries whose normal_hash + generation
        already exist in the DB are skipped.
        """
        imported = 0
        skipped = 0

        for row in rows:
            question = row["question"].strip()
            generation = int(row["generation"])
            response = row["response"].strip()

            if not question or not response:
                skipped += 1
                continue

            exact = _exact_hash(question)
            normal = _normal_hash(question)

            if skip_duplicates:
                existing = await self._fetchone(
                    "SELECT id FROM response_cache WHERE normal_hash = ? AND generation = ?",
                    (normal, generation),
                )
                if existing:
                    skipped += 1
                    continue

            await self._db.execute(
                """INSERT INTO response_cache
                   (exact_hash, normal_hash, question, generation, response)
                   VALUES (?, ?, ?, ?, ?)""",
                (exact, normal, question, generation, response),
            )
            imported += 1

        await self._db.commit()
        logger.info("Cache IMPORT: %d imported, %d skipped", imported, skipped)
        return {"imported": imported, "skipped": skipped}

    # ── Rehash (after normalization rule changes) ───────────────

    async def rehash_all(self) -> dict:
        """Recompute exact_hash and normal_hash for ALL entries.

        Call this after changing normalization rules (_STOPWORDS,
        _PLURAL_MAP, _GAME_TITLE_STOPWORDS, etc.) so that existing
        entries match queries hashed with the new rules.

        Returns count of updated entries and any duplicates found
        (entries that now produce the same normal_hash + generation).
        """
        cursor = await self._db.execute(
            "SELECT id, question, generation FROM response_cache ORDER BY id"
        )
        rows = await cursor.fetchall()

        updated = 0
        duplicates: list[dict] = []
        seen_hashes: dict[tuple[str, int], int] = {}  # (normal_hash, gen) → first id

        for r in rows:
            entry_id, question, generation = r[0], r[1], r[2]
            new_exact = _exact_hash(question)
            new_normal = _normal_hash(question)

            # Track duplicates: entries that now share the same normal_hash + gen
            key = (new_normal, generation)
            if key in seen_hashes:
                duplicates.append({
                    "id": entry_id,
                    "question": question[:80],
                    "generation": generation,
                    "duplicate_of_id": seen_hashes[key],
                    "normal_hash": new_normal[:16],
                })
            else:
                seen_hashes[key] = entry_id

            await self._db.execute(
                "UPDATE response_cache SET exact_hash = ?, normal_hash = ? WHERE id = ?",
                (new_exact, new_normal, entry_id),
            )
            updated += 1

        await self._db.commit()
        logger.info(
            "Cache REHASH: %d entries updated, %d duplicates found",
            updated, len(duplicates),
        )
        return {
            "updated": updated,
            "duplicates_found": len(duplicates),
            "duplicates": duplicates,
        }

    # ── Duplicate groups ────────────────────────────────────────

    async def list_duplicate_groups(
        self,
        generation: int | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """Find groups of entries that share the same (normal_hash, generation).

        Returns groups with their entries and the final tokens that produced
        the shared hash, so the admin can decide if they're true duplicates
        or false positives caused by incorrect stopword removal.
        """
        # Step 1: find hashes with more than 1 entry
        gen_clause = "AND generation = ?" if generation else ""
        gen_params: tuple = (generation,) if generation else ()

        count_cursor = await self._db.execute(
            f"""SELECT COUNT(*) FROM (
                SELECT normal_hash, generation
                FROM response_cache
                WHERE 1=1 {gen_clause}
                GROUP BY normal_hash, generation
                HAVING COUNT(*) > 1
            )""",
            gen_params,
        )
        total_groups = (await count_cursor.fetchone())[0]

        offset = (page - 1) * per_page
        group_cursor = await self._db.execute(
            f"""SELECT normal_hash, generation, COUNT(*) as cnt
                FROM response_cache
                WHERE 1=1 {gen_clause}
                GROUP BY normal_hash, generation
                HAVING COUNT(*) > 1
                ORDER BY cnt DESC, generation ASC
                LIMIT ? OFFSET ?""",
            gen_params + (per_page, offset),
        )
        group_rows = await group_cursor.fetchall()

        # Step 2: for each group, fetch its entries
        groups = []
        for g in group_rows:
            nhash, gen, cnt = g[0], g[1], g[2]
            entries_cursor = await self._db.execute(
                """SELECT id, question, hit_count, reviewed, feedback, created_at
                   FROM response_cache
                   WHERE normal_hash = ? AND generation = ?
                   ORDER BY hit_count DESC, id ASC""",
                (nhash, gen),
            )
            entry_rows = await entries_cursor.fetchall()

            # Compute final tokens from the first entry's question
            final_tokens = _compute_final_tokens(entry_rows[0][1]) if entry_rows else []

            entries = [
                {
                    "id": r[0],
                    "question": r[1],
                    "hit_count": r[2],
                    "reviewed": bool(r[3]),
                    "feedback": r[4],
                    "created_at": r[5],
                }
                for r in entry_rows
            ]

            groups.append({
                "normal_hash": nhash[:16],
                "generation": gen,
                "count": cnt,
                "final_tokens": final_tokens,
                "entries": entries,
            })

        return {
            "groups": groups,
            "total_groups": total_groups,
            "page": page,
            "per_page": per_page,
        }

    # ── Export ────────────────────────────────────────────────────

    async def export_all(self) -> list[dict]:
        """Export all cache entries as a list of dicts (for CSV export)."""
        cursor = await self._db.execute(
            """SELECT id, question, generation, response, hit_count,
                      reviewed, exact_hash, normal_hash,
                      created_at, last_hit_at, reviewed_at, feedback
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
                "feedback": r[11],
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

        # Step 2a: plurals
        tokens = [_PLURAL_MAP.get(t, t) for t in tokens]
        after_plurals = list(tokens)

        # Step 2b: strategic intent normalization
        tokens = [_STRATEGIC_SYNONYM_MAP.get(t, t) for t in tokens]
        after_strategic = list(tokens)

        # Step 3: gen numbers
        gen_number_indices: set[int] = set()
        for i, t in enumerate(tokens):
            if t in _GEN_KEYWORDS:
                if i > 0 and tokens[i - 1].isdigit():
                    gen_number_indices.add(i - 1)
                if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                    gen_number_indices.add(i + 1)

        # Step 3c: conditional game title tokens
        conditional_indices = _find_conditional_indices(tokens)

        # Step 4: filter (must match _normal_hash exactly)
        all_stopwords = _STOPWORDS | _custom_stopwords
        filtered = sorted(set(
            t for i, t in enumerate(tokens)
            if t not in all_stopwords
            and t not in _GAME_TITLE_STOPWORDS
            and len(t) >= 2
            and i not in gen_number_indices
            and i not in conditional_indices
        ))

        # Identify removed tokens for debug output
        builtin_stopwords_found = [
            t for t in tokens if t in _STOPWORDS
        ]
        custom_stopwords_found = [
            t for t in tokens if t in _custom_stopwords
        ]
        game_titles_found = [
            t for t in tokens if t in _GAME_TITLE_STOPWORDS
        ]
        conditional_found = [
            tokens[i] for i in sorted(conditional_indices)
        ]

        return {
            "question": question,
            "generation": generation,
            "exact_hash": _exact_hash(question)[:16],
            "normal_hash": _normal_hash(question)[:16],
            "pipeline": {
                "0_after_gen_split": after_split,
                "1_after_ordinals": after_ordinals,
                "2a_after_plurals": after_plurals,
                "2b_after_strategic": after_strategic,
                "3_gen_numbers_removed": sorted(gen_number_indices),
                "3b_game_titles_removed": game_titles_found,
                "3c_conditional_removed": conditional_found,
                "3d_builtin_stopwords_removed": builtin_stopwords_found,
                "3e_custom_stopwords_removed": custom_stopwords_found,
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
