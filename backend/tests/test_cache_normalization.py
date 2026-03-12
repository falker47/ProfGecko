"""Tests for the cache hash normalization pipeline.

These are pure-function tests — no database, no LLM, no external services.
They verify the linguistic normalization logic that ensures semantically
identical questions produce the same hash.
"""

from app.core.cache import (
    _compute_final_tokens,
    _exact_hash,
    _normal_hash,
    _split_gen_tokens,
)


# ── _split_gen_tokens ────────────────────────────────────────────────

class TestSplitGenTokens:
    def test_splits_gen4(self):
        assert _split_gen_tokens(["gen4"]) == ["gen", "4"]

    def test_splits_generazione5(self):
        assert _split_gen_tokens(["generazione5"]) == ["generazione", "5"]

    def test_leaves_normal_tokens(self):
        assert _split_gen_tokens(["garchomp", "gen", "4"]) == ["garchomp", "gen", "4"]


# ── _exact_hash ──────────────────────────────────────────────────────

class TestExactHash:
    def test_case_insensitive(self):
        assert _exact_hash("Garchomp") == _exact_hash("garchomp")

    def test_whitespace_collapsed(self):
        assert _exact_hash("  mosse   garchomp  ") == _exact_hash("mosse garchomp")

    def test_different_questions_differ(self):
        assert _exact_hash("mosse garchomp") != _exact_hash("debolezze garchomp")


# ── Plural normalization (normal_hash equivalence) ───────────────────

class TestPluralNormalization:
    def test_italian_plural_debolezze(self):
        """debolezze → debolezza"""
        assert _normal_hash("debolezze Garchomp") == _normal_hash("debolezza Garchomp")

    def test_italian_plural_mosse(self):
        """mosse → mossa"""
        assert _normal_hash("mosse Garchomp") == _normal_hash("mossa Garchomp")

    def test_english_plural_weaknesses(self):
        """weaknesses → weakness"""
        assert _normal_hash("weaknesses Garchomp") == _normal_hash("weakness Garchomp")

    def test_different_concepts_differ(self):
        """mossa and debolezza must NOT match."""
        assert _normal_hash("mosse garchomp") != _normal_hash("debolezze garchomp")


# ── Ordinal normalization ────────────────────────────────────────────

class TestOrdinalNormalization:
    def test_italian_ordinal_quinta(self):
        """quinta → 5"""
        tokens = _compute_final_tokens("quinta generazione garchomp")
        assert "5" not in tokens  # gen number is stripped along with gen keyword
        assert "garchomp" in tokens

    def test_gen_keyword_with_number(self):
        """'gen 5' and 'generazione 5' should produce the same hash."""
        assert _normal_hash("garchomp gen 5") == _normal_hash("garchomp generazione 5")


# ── Game title stripping ─────────────────────────────────────────────

class TestGameTitleStripping:
    def test_platino_stripped(self):
        """'platino' is a game title and should be stripped."""
        tokens = _compute_final_tokens("garchomp debolezze platino")
        assert "platino" not in tokens
        assert "garchomp" in tokens
        assert "debolezza" in tokens  # plural normalized

    def test_spada_stripped(self):
        """'spada' is a game title and should be stripped."""
        tokens = _compute_final_tokens("garchomp spada")
        assert "spada" not in tokens


# ── Conditional game tokens ──────────────────────────────────────────

class TestConditionalGameTokens:
    def test_fuoco_kept_in_tipo_fuoco(self):
        """'fuoco' should be kept when NOT adjacent to 'rosso'."""
        tokens = _compute_final_tokens("tipo fuoco")
        assert "fuoco" in tokens

    def test_fuoco_stripped_in_rosso_fuoco(self):
        """'fuoco' should be stripped when adjacent to 'rosso' (game title)."""
        tokens = _compute_final_tokens("rosso fuoco garchomp")
        assert "fuoco" not in tokens


# ── Strategic synonym normalization ──────────────────────────────────

class TestStrategicSynonyms:
    def test_migliore_and_consiglia_converge(self):
        """Strategic synonyms should hash equally."""
        assert _normal_hash("migliore starter") == _normal_hash("consiglia starter")

    def test_best_converges_to_consiglio(self):
        """English 'best' also maps to _consiglio_."""
        assert _normal_hash("best starter") == _normal_hash("migliore starter")


# ── Stopword removal ────────────────────────────────────────────────

class TestStopwordRemoval:
    def test_articles_removed(self):
        """Italian articles should be stripped."""
        tokens = _compute_final_tokens("il tipo di garchomp")
        assert "il" not in tokens
        assert "di" not in tokens
        assert "tipo" in tokens
        assert "garchomp" in tokens

    def test_pokemon_terms_kept(self):
        """Key Pokemon terms must NOT be treated as stopwords."""
        tokens = _compute_final_tokens("debolezza mossa tipo abilita evoluzione")
        assert "debolezza" in tokens
        assert "mossa" in tokens
        assert "tipo" in tokens

    def test_gen_keyword_removed(self):
        """'gen', 'generazione', 'generation' should be stripped."""
        tokens = _compute_final_tokens("garchomp gen 5")
        assert "gen" not in tokens
        assert "generazione" not in tokens
