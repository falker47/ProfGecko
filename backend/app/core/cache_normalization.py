"""Normalization constants for the response cache hash pipeline.

All linguistic data (stopwords, synonyms, ordinals, game titles) used
by the two-level hash matching system in cache.py.  Kept in a separate
file so editing a stopword or synonym never touches DB / hashing logic.
"""

# ── Stopwords — ONLY generic words, NOT Pokemon-specific terms ──────
# Pokemon terms (debolezza, mossa, tipo, abilita, etc.) are
# semantically important and MUST stay in the hash to prevent
# false positives (e.g. "mosse garchomp" ≠ "debolezze garchomp").

STOPWORDS: frozenset[str] = frozenset({
    # Italian — articles, prepositions, pronouns, conjunctions
    "il", "lo", "la", "le", "li", "un", "una", "uno", "gli", "dei", "dammi",
    "del", "della", "delle", "degli", "dettagli", "nel", "nella", "nelle", "nei",
    "negli", "sul", "sulla", "sulle", "al", "alla", "alle", "ai",
    "che", "chi", "ci", "per", "con", "tra", "far", "fare", "fra", "non", "piu", "più", "di", "mi",
    "come", "cosa", "quali", "quale", "qual", "si", "sono", "suo", "sua",
    "suoi", "sue", "questo", "questa", "quello", "quella", "questi",
    "queste", "quanti", "quante", "quanto", "do", "mio",
    "tutto", "tutta", "tutti", "tutte",
    "molto", "poco", "troppo", "anche", "ancora", "tanto", "così", "cosi",
    "su", "nei", "oppure",
    "perché", "perche", "perchè",  # interrogative / conjunction
    # Italian — common verbs / filler in questions
    "hanno", "ha", "hai", "puoi", "può", "fa", "vai", "vorrei", "sapere",
    "parlami", "dimmi", "mostrami", "spiegami", "descrivi", "elenca",
    "confronta", "confronto", "vincerebbe", "scontro",
    "funziona", "funzionano", "impara", "apprende", "possiede",
    "affrontare", "avventura",
    "cos",  # from "cos'è" (tokenized as "cos" + "è")
    # NOTE: parole strategiche (consiglio, meglio, conviene, etc.) e
    # trainer (capipalestra, superquattro, etc.) NON sono stopwords.
    # Vengono normalizzate a token canonici in STRATEGIC_SYNONYM_MAP
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

ORDINAL_MAP: dict[str, str] = {
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

PLURAL_MAP: dict[str, str] = {
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

STRATEGIC_SYNONYM_MAP: dict[str, str] = {
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
    "converrebbe": "_consiglio_",
    "suggerimento": "_consiglio_",
    "suggerimenti": "_consiglio_",
    "suggerisci": "_consiglio_",
    "suggerire": "_consiglio_",
    "suggerito": "_consiglio_",
    "suggerita": "_consiglio_",
    "suggerirei": "_consiglio_",
    "suggerirebbe": "_consiglio_",
    "suggerirebbero": "_consiglio_",
    "proponi": "_consiglio_",
    "proporresti": "_consiglio_",
    "proporrebbe": "_consiglio_",
    # EN — advisory intent → _consiglio_
    "suggestion": "_consiglio_",
    "suggest": "_consiglio_",
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

GEN_KEYWORDS: frozenset[str] = frozenset({"gen", "generazione", "generation"})

# ── Game title stopwords ──────────────────────────────────────────
# Game titles are stripped because the generation is already stored
# as a separate DB column. This way "garchomp debolezze platino"
# matches "garchomp debolezze gen 4" (both → gen=4, hash=same tokens).
# Excluded from this set: words that overlap with Pokemon type/move
# terms (fuoco, fire, leaf, green) — these are handled conditionally
# via CONDITIONAL_GAME_TOKENS below.
# Also excluded: pikachu/eevee/arceus (Pokemon names in game titles).

GAME_TITLE_STOPWORDS: frozenset[str] = frozenset({
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

CONDITIONAL_GAME_TOKENS: dict[str, frozenset[str]] = {
    # "rosso fuoco" / "verde foglia" (IT gen 3)
    "fuoco": frozenset({"rosso"}),
    # "fire red" / "leaf green" (EN gen 3)
    "fire": frozenset({"red"}),
    "leaf": frozenset({"green"}),
    "green": frozenset({"leaf"}),
}
