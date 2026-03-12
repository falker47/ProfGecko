import logging
import re

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.cache import ResponseCache
from app.core.generation_mapper import LATEST_GENERATION, detect_game_slug, detect_generation
from app.core.prompts import PROF_GECKO_STRATEGIC_PROMPT, PROF_GECKO_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# --- Entity-type intent detection ---
# Items e nature vengono esclusi dal retrieval di default perche'
# sommergono i risultati per le query su Pokemon/mosse/tipi/abilita'.
# Vengono inclusi solo quando l'utente li chiede esplicitamente.

_ITEM_KEYWORDS = frozenset({
    "strumento", "strumenti", "oggetto", "oggetti",
    "bacca", "bacche", "item", "items", "berry", "berries",
    "pietra", "held item",
    "mt", "mn", "tm", "hm",
    "megapietra", "megapietre", "mega stone", "mega stones",
    "cristallo z", "z crystal",
})
_NATURE_KEYWORDS = frozenset({
    "natura", "nature", "natures", "indole",
    "carattere", "personalita", "personalità",
})

# Keywords that trigger game_info document injection
_GAME_INFO_KEYWORDS = frozenset({
    "starter", "iniziale", "iniziali", "quale scegliere",
    "squadra", "team", "pokemon da usare",
    "esclusivo", "esclusivi", "esclusiva", "exclusive",
    "solo in", "differenze versione",
    "leggendario", "leggendari", "mitico", "mitici",
    # Sinonimi aggiuntivi
    "completare", "finire", "playthrough",
    "party", "formazione",
})

# Encounter documents are excluded by default (like items/natures) to prevent
# them from flooding semantic search results. Only included when the user
# explicitly asks about locations or catching.
_ENCOUNTER_KEYWORDS = frozenset({
    "dove", "trovare", "catturare", "cattura",
    "percorso", "route", "grotta", "foresta",
    "luogo", "posizione", "zona", "encounter",
    "dove si trova", "dove trovo", "dove catturare",
    "trovo", "trova", "ottengo", "ottenere", "prendere",
    "beccare", "location", "incontro", "selvatico", "selvatici",
    # Sinonimi aggiuntivi
    "reperire", "reperibile", "scovare", "pescare", "pesca",
    "compare", "appare", "avvistare", "cacciare",
    "catturabile", "ottenibile",
})

# Cross-generational availability queries — triggers retrieval of
# generation-0 availability documents that span all games.
_AVAILABILITY_KEYWORDS = frozenset({
    "in quali giochi", "in quale gioco",
    "in quali versioni", "in quale versione",
    "in which games", "in which versions",
    "in che gioco", "in che versione",
    "disponibile", "disponibilita", "disponibili", "disponibilità",
    "giochi", "versioni",
    # Sinonimi cross-generazionali
    "presente", "assente",
    "esiste in", "compare in",
})

# Smogon competitive sets: excluded by default, included when the user
# asks about competitive builds or uses Smogon-specific terms.
_SMOGON_KEYWORDS = frozenset({
    "smogon", "set competitivo", "set competitivi",
    "build competitiva", "build competitive",
    "ev spread", "moveset smogon", "set smogon",
    "build smogon",
    "tier ou", "tier uu", "tier ubers", "tier ru", "tier nu",
    "overused", "underused", "neverused", "rarelyused",
})

# Stop words italiane da ignorare nell'estrazione nomi entita.
# NOTA: l'estrazione lavora in lowercase, quindi tutte le stop words
# devono essere lowercase.
_STOP_WORDS = frozenset({
    # Articoli, preposizioni, pronomi
    "che", "chi", "per", "con", "del", "della", "delle", "dei", "degli",
    "nel", "nella", "nelle", "nei", "negli", "sul", "sulla", "sulle",
    "come", "cosa", "quali", "quale", "sono", "una", "uno", "gli", "non",
    "tra", "fra", "piu", "suo", "sua", "suoi", "sue", "questo", "questa",
    "quello", "quella", "molto", "poco", "troppo", "anche", "ancora",
    # Verbi comuni nelle domande
    "parlami", "dimmi", "mostrami", "spiegami", "descrivi", "elenca",
    "confronta", "confronto", "vincerebbe", "scontro", "meglio",
    "impara", "apprende", "evolve",
    # Strategic query terms
    "squadra", "team", "build", "set", "moveset", "starter",
    "consiglio", "consigli", "consigliata", "consigliato", "consiglia",
    "suggerisci", "suggerimento", "suggerimenti", "suggerita", "suggerito",
    "ideale", "ottimale", "perfetto", "perfetta",
    "strategia", "competitivo", "counter", "contrastare",
    "avventura", "conviene", "alternativa", "alternative",
    "vantaggi", "svantaggi",
    "formazione", "party", "roster", "composizione",
    "completare", "finire", "playthrough",
    # Trainer / gym terms
    "capopalestra", "capipalestra", "superquattro",
    "campione", "champion", "palestra", "lega",
    # Game info terms
    "iniziale", "iniziali", "esclusivo", "esclusivi",
    "leggendario", "leggendari",
    # Game title words (prevent game names from being name candidates)
    "rosso", "blu", "giallo", "oro", "argento", "cristallo",
    "rubino", "zaffiro", "smeraldo",
    "diamante", "perla", "platino",
    "nero", "bianco",
    "sole", "luna", "ultrasole", "ultraluna",
    "spada", "scudo",
    "scarlatto", "violetto",
    # Remake game title words
    "foglia", "fuoco", "omega", "alpha",
    "lucente", "splendente", "leggende",
    "heartgold", "soulsilver",
    # Breeding / egg group terms
    "gruppo", "uova", "uovo", "breeding", "accoppiamento",
    # Regional variant terms (adjectives only, not region names)
    "alolano", "alolana", "forma",
    "galariano", "galariana",
    "hisuiano", "hisuiana",
    "paldeano", "paldeana",
    "regionale", "regionali", "variante", "varianti",
    # Encounter/location terms
    "dove", "trovare", "catturare", "cattura",
    "percorso", "route", "grotta", "foresta",
    "luogo", "posizione", "zona",
    "trovo", "trova", "ottengo", "ottenere", "prendere",
    "beccare", "selvatico", "selvatici", "incontro",
    "reperire", "reperibile", "scovare", "pescare", "pesca",
    "cacciare", "avvistare", "catturabile", "ottenibile",
    # Availability/cross-gen terms
    "giochi", "versioni", "disponibile", "disponibili",
    "disponibilita", "presente", "assente",
    # Termini Pokemon generici
    "pokemon", "pokémon",
    "tipo", "tipi", "mossa", "mosse", "abilita", "abilità", "stat", "statistiche",
    "debolezze", "debolezza", "resistenze", "resistenza", "immunita", "immunità",
    "generazione", "gen", "catena", "evolutiva", "evoluzione",
    "base", "totale", "velocita", "velocità", "attacco", "difesa", "speciale",
    # Sinonimi termini Pokemon
    "tecnica", "tecniche",  # sinonimo di mossa
    "talento", "potere",  # sinonimo di abilita
    "vulnerabile", "vulnerabilita", "punto",  # sinonimo di debolezza
    "carattere", "personalita", "indole", "natura",  # sinonimo di nature
    "elemento", "tipologia",  # sinonimo di tipo
    # Verbi/termini aggiuntivi
    "qual", "quando", "quanti", "quante",
    "tasso", "crescita",
})

# Soglia parole per considerare una domanda auto-contenuta (non un follow-up).
# Domande con piu' parole di questa soglia non vengono arricchite con
# contesto dalla chat history per evitare cross-contamination.
_SELF_CONTAINED_WORD_COUNT = 6

# Phrase used by the LLM when context doesn't contain the answer.
# Matched (lowercase) against response text to auto-flag as feedback='M'.
_MISSING_PHRASE = "non ho questa informazione"

# --- Analytical query detection ---
# Maps keyword patterns to summary_category values for targeted retrieval.
# When a query contains these keywords (and no specific Pokemon name),
# the retriever fetches pre-computed summary docs instead of individual Pokemon.
_SUMMARY_KEYWORD_MAP: list[tuple[list[str], list[str]]] = [
    # (keyword patterns, summary_categories to fetch)
    (
        ["piu forte", "piu forti", "migliore", "migliori", "classifica",
         "ranking", "top", "potente", "potenti"],
        ["bst_ranking_overall", "bst_ranking_non_legendary"],
    ),
    (
        ["piu veloce", "piu veloci", "velocita"],
        ["stat_ranking_speed"],
    ),
    (
        ["piu attacco", "attacco fisico piu alto", "attacco piu alto"],
        ["stat_ranking_atk"],
    ),
    (
        ["piu difesa", "difesa fisica piu alta", "difesa piu alta"],
        ["stat_ranking_defense"],
    ),
    (
        ["attacco speciale piu alto", "piu attacco speciale"],
        ["stat_ranking_spatk"],
    ),
    (
        ["difesa speciale piu alta", "piu difesa speciale"],
        ["stat_ranking_spdef"],
    ),
    (
        ["piu hp", "piu vita", "piu punti salute", "punti vita piu alti",
         "hp piu alti"],
        ["stat_ranking_hp"],
    ),
    (
        ["leggendari", "leggendario", "mitici", "mitico"],
        ["legendary_mythical_list"],
    ),
    (
        ["quanti pokemon", "distribuzione", "tipo piu comune",
         "tipo piu raro", "tipi piu comuni"],
        ["type_distribution"],
    ),
    (
        ["squadra", "team", "roster", "composizione", "formazione", "party"],
        ["team_roster_by_role"],
    ),
    (
        ["mega evoluzione", "megaevoluzione", "mega evoluzioni",
         "megaevoluzioni", "mega evolution", "mega evolutions",
         "quante mega", "lista mega", "mega stone", "megapietre"],
        ["mega_evolution_list"],
    ),
]


def _detect_summary_categories(question: str) -> list[str]:
    """Detect which summary categories are relevant for an analytical query.

    Returns a list of summary_category values to fetch, or empty list
    if the query is not analytical.
    """
    q = question.lower()
    categories: list[str] = []
    for keywords, cats in _SUMMARY_KEYWORD_MAP:
        if any(kw in q for kw in keywords):
            for cat in cats:
                if cat not in categories:
                    categories.append(cat)
    return categories


def _detect_excluded_types(question: str) -> list[str]:
    """Determina quali entity_type escludere dal retrieval ChromaDB.

    Di default esclude 'item', 'nature', 'encounter' e 'smogon_set'.
    Li include solo se la domanda contiene keyword specifiche.
    smogon_set viene incluso anche per query strategiche (build, team, ...).
    """
    q = question.lower()
    excluded: list[str] = []
    if not any(kw in q for kw in _ITEM_KEYWORDS):
        excluded.append("item")
    if not any(kw in q for kw in _NATURE_KEYWORDS):
        excluded.append("nature")
    if not any(kw in q for kw in _ENCOUNTER_KEYWORDS):
        excluded.append("encounter")
    # Availability docs (cross-gen) are only included for availability queries
    if not any(kw in q for kw in _AVAILABILITY_KEYWORDS):
        excluded.append("availability")
    # Include Smogon sets when: explicit Smogon keywords OR strategic query
    if not any(kw in q for kw in _SMOGON_KEYWORDS) and not _is_strategic_query(q):
        excluded.append("smogon_set")
    return excluded


# --- Strategic query detection ---
_STRATEGIC_KEYWORDS: list[str] = [
    # Team building
    "squadra", "team", "roster", "composizione", "formazione", "party",
    # Build / moveset
    "build", "moveset", "miglior set",
    # Advice
    "consigliata", "consigliato", "consigli", "consiglio", "consiglia",
    "suggerisci", "suggerimento", "suggerimenti", "suggerita", "suggerito",
    # Best / optimal
    "ideale", "ottimale", "perfetto", "perfetta",
    # Starter
    "starter", "iniziale", "quale scegliere",
    # Strategy
    "strategia", "competitivo", "competitive",
    "counter", "contrastare",
    # Usage
    "come usare", "come si usa", "come sfruttare",
    "conviene", "vale la pena",
    # Pros / cons
    "pro e contro", "vantaggi", "svantaggi",
    "alternativa", "alternative",
    # In-game playthrough
    "avventura", "playthrough", "completare", "finire",
    # Trainers / gym leaders
    "capopalestra", "capipalestra", "superquattro", "elite four",
    "campione", "champion", "palestra", "lega",
]


def _is_strategic_query(question: str) -> bool:
    """Detect if a question requires strategic reasoning (builds, teams, advice)."""
    q = question.lower()
    return any(kw in q for kw in _STRATEGIC_KEYWORDS)


# Region names used for compound variant name construction
_REGION_NAMES = frozenset({"alola", "galar", "hisui", "paldea"})


def _extract_candidate_names(question: str) -> list[str]:
    """Estrae parole candidate come nomi di entita dalla domanda.

    Ritorna parole di almeno 3 caratteri, rimuovendo stop words e
    punteggiatura. Usato per il matching diretto sui metadata ChromaDB.

    Quando rileva una regione (alola, galar, hisui, paldea) insieme a un
    nome Pokemon, costruisce anche il nome composto "pokemon-regione"
    (es. "raichu-alola") per matchare le varianti regionali.
    """
    words = re.findall(r"[a-zA-ZÀ-ÿ\-]+", question.lower())
    base_candidates = [
        w for w in words
        if len(w) >= 3 and w not in _STOP_WORDS
    ]

    # Detect regional names in the question (these are NOT in _STOP_WORDS)
    regions_found = [w for w in base_candidates if w in _REGION_NAMES]
    non_region = [w for w in base_candidates if w not in _REGION_NAMES]

    # Build compound names: "pokemon-region" (e.g. "raichu-alola")
    if regions_found and non_region:
        compound_names = []
        for name in non_region:
            for region in regions_found:
                compound_names.append(f"{name}-{region}")
        # Put compound names first (more specific), then individual names
        return compound_names + non_region
    return base_candidates


# Keywords that indicate a team-building query (subset of _STRATEGIC_KEYWORDS)
_TEAM_KEYWORDS = frozenset({
    "squadra", "team", "roster", "composizione",
    "formazione", "party",
})


def _extract_team_pokemon_names(text: str) -> list[str]:
    """Extract Pokemon names from team recommendation text.

    Handles bullet-list formats commonly used in team_roster and
    best_team documents:
      "- Darmanitan (Fuoco) - desc"
      "- Darmanitan: Fuoco, Atk 140, ..."
      "- Darmanitan: Fuoco/Veleno, BST 480, Sweeper [Leggendario]"

    Returns lowercased names, deduplicated and in order of appearance.
    """
    seen: set[str] = set()
    names: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line.startswith("- "):
            continue
        rest = line[2:].strip()
        match = re.match(r"([a-zA-ZÀ-ÿ][\w\-]*)", rest)
        if match:
            name = match.group(1).lower()
            if len(name) >= 3 and name not in _STOP_WORDS and name not in seen:
                seen.add(name)
                names.append(name)
    return names


def _format_docs(docs: list[Document]) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


def _convert_chat_history(
    messages: list[dict],
) -> list[HumanMessage | AIMessage]:
    result = []
    for msg in messages:
        if msg["role"] == "user":
            result.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            result.append(AIMessage(content=msg["content"]))
    return result


class RAGChain:
    """RAG chain with generation-aware retrieval."""

    def __init__(
        self,
        llm: BaseChatModel,
        vectorstore: Chroma,
        k: int = 5,
        fallback_llm: BaseChatModel | None = None,
    ):
        self.llm = llm
        self.fallback_llm = fallback_llm
        self.vectorstore = vectorstore
        self.k = k

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", PROF_GECKO_SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{question}"),
        ])

        self.strategic_prompt = ChatPromptTemplate.from_messages([
            ("system", PROF_GECKO_STRATEGIC_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{question}"),
        ])

        self.output_parser = StrOutputParser()

    def _build_retrieval_query(
        self, question: str, chat_history: list[dict],
    ) -> str:
        """Arricchisce la query con contesto dalla chat history per follow-up brevi.

        Per follow-up brevi (es. "e le mosse?", "e in terza gen?"), aggiunge
        contesto dall'ultimo messaggio utente. Per domande gia' specifiche
        (es. "Garchomp in Platino che debolezze ha?"), usa la domanda cosi'
        com'e' per evitare cross-contamination con il contesto precedente.

        Usa il conteggio parole (>= 6 parole = auto-contenuta) invece di
        un limite caratteri, piu' robusto per query italiane.

        La domanda corrente viene messa PRIMA del contesto per dare piu'
        peso semantico all'embedding della query attuale.
        """
        if not chat_history:
            return question

        word_count = len(question.split())
        if word_count >= _SELF_CONTAINED_WORD_COUNT:
            return question

        # Per follow-up brevi, aggiungi contesto (domanda corrente PRIMA)
        for msg in reversed(chat_history):
            if msg["role"] == "user":
                return f"{question} {msg['content']}"
        return question

    def _find_by_name(
        self,
        question: str,
        generation: int,
        retrieval_query: str | None = None,
    ) -> list[Document]:
        """Cerca documenti il cui nome (IT o EN) matcha parole nella domanda.

        Risolve il problema dell'embedding dilution: i documenti Pokemon
        sono troppo lunghi (~1400 chars) per il modello di embedding
        (max 128 token), quindi il nome si perde nell'embedding.
        Il matching diretto sui metadata bypassa completamente il problema.

        Controlla sia la domanda originale che la retrieval query arricchita
        (per gestire follow-up come "che debolezze ha?" dove il nome del
        Pokemon e' nella chat history, non nella domanda).
        """
        candidates = _extract_candidate_names(question)
        if retrieval_query and retrieval_query != question:
            for name in _extract_candidate_names(retrieval_query):
                if name not in candidates:
                    candidates.append(name)
        if not candidates:
            return []

        collection = self.vectorstore._collection
        found_docs: list[Document] = []
        found_ids: set[str] = set()

        for name in candidates:
            try:
                results = collection.get(
                    where={
                        "$and": [
                            {"generation": generation},
                            {"$or": [
                                {"name_it": name},
                                {"name_en": name},
                            ]},
                        ],
                    },
                    include=["documents", "metadatas"],
                )
            except Exception:
                logger.warning("Chroma name-match query failed for %r", name, exc_info=True)
                continue

            for j, doc_id in enumerate(results["ids"]):
                if doc_id not in found_ids:
                    found_ids.add(doc_id)
                    found_docs.append(Document(
                        page_content=results["documents"][j],
                        metadata=results["metadatas"][j],
                    ))

        if found_docs:
            logger.info(
                "Name match for %r: found %d docs: %s",
                candidates,
                len(found_docs),
                [(d.metadata.get("entity_type"), d.metadata.get("name_it"))
                 for d in found_docs],
            )
        return found_docs

    def _find_summaries(
        self,
        question: str,
        generation: int,
    ) -> list[Document]:
        """Cerca documenti riassuntivi per domande analitiche/classifiche.

        Quando la domanda contiene keyword come "piu forte", "classifica",
        "leggendari", etc., recupera i documenti summary pre-computati
        per categoria. Questi non vengono trovati dal name matching
        (nome troppo generico) ne dalla semantic search (embedding dilution
        con centinaia di documenti Pokemon individuali).
        """
        categories = _detect_summary_categories(question)
        if not categories:
            return []

        collection = self.vectorstore._collection
        found_docs: list[Document] = []
        found_ids: set[str] = set()

        for cat in categories:
            try:
                results = collection.get(
                    where={
                        "$and": [
                            {"generation": generation},
                            {"entity_type": "summary"},
                            {"summary_category": cat},
                        ],
                    },
                    include=["documents", "metadatas"],
                )
            except Exception:
                logger.warning("Chroma summary query failed for category %r", cat, exc_info=True)
                continue

            for j, doc_id in enumerate(results["ids"]):
                if doc_id not in found_ids:
                    found_ids.add(doc_id)
                    found_docs.append(Document(
                        page_content=results["documents"][j],
                        metadata=results["metadatas"][j],
                    ))

        if found_docs:
            logger.info(
                "Summary match for %r: found %d docs: %s",
                categories,
                len(found_docs),
                [d.metadata.get("summary_category") for d in found_docs],
            )
        return found_docs

    def _find_summaries_by_category(
        self, category: str, generation: int,
    ) -> list[Document]:
        """Fetch a specific summary category directly (for strategic fallback)."""
        collection = self.vectorstore._collection
        try:
            results = collection.get(
                where={
                    "$and": [
                        {"generation": generation},
                        {"entity_type": "summary"},
                        {"summary_category": category},
                    ],
                },
                include=["documents", "metadatas"],
            )
        except Exception:
            logger.warning("Chroma query failed for summary category %r", category, exc_info=True)
            return []
        docs = []
        for j, _doc_id in enumerate(results["ids"]):
            docs.append(Document(
                page_content=results["documents"][j],
                metadata=results["metadatas"][j],
            ))
        return docs

    def _find_trainer_docs(self, generation: int) -> list[Document]:
        """Fetch trainer_info documents (gym leaders, E4, champion) for a generation.

        Used for strategic queries to provide accurate gym leader / Elite Four
        data instead of letting the LLM hallucinate matchups.
        """
        collection = self.vectorstore._collection
        try:
            results = collection.get(
                where={
                    "$and": [
                        {"generation": generation},
                        {"entity_type": "trainer_info"},
                    ],
                },
                include=["documents", "metadatas"],
            )
        except Exception:
            logger.warning("Chroma query failed for trainer_info gen=%d", generation, exc_info=True)
            return []
        docs = []
        for j, _doc_id in enumerate(results["ids"]):
            docs.append(Document(
                page_content=results["documents"][j],
                metadata=results["metadatas"][j],
            ))
        if docs:
            logger.info(
                "Trainer docs for gen %d: found %d docs (%s)",
                generation,
                len(docs),
                [d.metadata.get("game_it", "?") for d in docs],
            )
        return docs

    def _find_game_info_docs(
        self, generation: int, question: str,
        game_slug: str | None = None,
    ) -> list[Document]:
        """Fetch game_info documents (starters, exclusives, legendaries).

        When game_slug is provided (e.g. "platinum"), filters to that
        specific game's documents. Otherwise returns all game_info docs
        for the generation.
        """
        collection = self.vectorstore._collection
        q = question.lower()

        # Determine which categories to fetch based on keywords
        categories: list[str] = []

        # Detect "best/recommendation" intent
        _best_kw = ("miglior", "migliore", "migliori", "best",
                     "consiglio", "consigliato", "consigliata",
                     "quale scegliere", "chi scegliere",
                     "suggerisci", "suggerimento", "suggerimenti",
                     "ideale", "ottimale", "perfetto", "perfetta")
        is_best = any(kw in q for kw in _best_kw)

        if any(kw in q for kw in ("starter", "iniziale", "iniziali")):
            categories.append("best_starter" if is_best else "starters")
        if any(kw in q for kw in ("squadra", "team", "pokemon da usare",
                                   "party", "formazione",
                                   "completare", "finire", "playthrough")):
            categories.append("best_team" if is_best else "starters")

        if any(kw in q for kw in ("esclusivo", "esclusivi", "esclusiva", "exclusive",
                                   "solo in", "differenze versione")):
            categories.append("version_exclusives")
        if any(kw in q for kw in ("leggendario", "leggendari", "mitico", "mitici",
                                   "dove trovare", "dove catturare")):
            categories.append("legendaries")

        if not categories:
            return []

        try:
            conditions: list[dict] = [
                {"generation": generation},
                {"entity_type": "game_info"},
            ]

            # Filter by specific game if detected
            if game_slug:
                conditions.append({"game_slug": game_slug})

            if len(categories) == 1:
                conditions.append({"info_category": categories[0]})
            else:
                conditions.append({"info_category": {"$in": categories}})

            where_filter = {"$and": conditions}
            results = collection.get(
                where=where_filter,
                include=["documents", "metadatas"],
            )
        except Exception:
            logger.warning("Chroma query failed for game_info categories=%r", categories, exc_info=True)
            return []

        docs = []
        for j, _doc_id in enumerate(results["ids"]):
            docs.append(Document(
                page_content=results["documents"][j],
                metadata=results["metadatas"][j],
            ))
        if docs:
            logger.info(
                "Game info docs for gen %d (game=%s): found %d docs (categories: %s)",
                generation,
                game_slug or "all",
                len(docs),
                categories,
            )
        return docs

    def _find_availability_docs(
        self,
        question: str,
        retrieval_query: str | None = None,
    ) -> list[Document]:
        """Fetch cross-generational availability documents (generation: 0).

        Used when the user asks "in quali giochi posso catturare X" — retrieves
        the aggregated availability doc that spans all generations.
        """
        q = question.lower()
        if not any(kw in q for kw in _AVAILABILITY_KEYWORDS):
            return []

        candidates = _extract_candidate_names(question)
        if retrieval_query and retrieval_query != question:
            for name in _extract_candidate_names(retrieval_query):
                if name not in candidates:
                    candidates.append(name)
        if not candidates:
            return []

        collection = self.vectorstore._collection
        found_docs: list[Document] = []
        found_ids: set[str] = set()

        for name in candidates:
            try:
                results = collection.get(
                    where={
                        "$and": [
                            {"generation": 0},
                            {"entity_type": "availability"},
                            {"$or": [
                                {"name_it": name},
                                {"name_en": name},
                            ]},
                        ],
                    },
                    include=["documents", "metadatas"],
                )
            except Exception:
                logger.warning(
                    "Chroma availability query failed for %r",
                    name, exc_info=True,
                )
                continue

            for j, doc_id in enumerate(results["ids"]):
                if doc_id not in found_ids:
                    found_ids.add(doc_id)
                    found_docs.append(Document(
                        page_content=results["documents"][j],
                        metadata=results["metadatas"][j],
                    ))

        if found_docs:
            logger.info(
                "Availability docs for %r: found %d docs",
                candidates, len(found_docs),
            )
        return found_docs

    def _retrieve(
        self,
        retrieval_query: str,
        generation: int,
        original_question: str,
        is_strategic: bool = False,
    ) -> list[Document]:
        """Recupera documenti con strategia ibrida a 3 fasi.

        1. Summary matching: per domande analitiche, recupera i documenti
           riassuntivi pre-computati (classifiche, distribuzioni tipo, etc.)
        2. Name matching: cerca entita il cui nome appare nella domanda
           (risolve l'embedding dilution dei documenti lunghi)
        3. Semantic search: riempie i posti rimanenti con risultati
           semanticamente rilevanti (cattura contesto aggiuntivo)

        Per domande strategiche (build, squadra, consigli): k viene aumentato
        di 6 per fornire più contesto al LLM.
        """
        q_lower = original_question.lower()
        is_team_query = is_strategic and any(kw in q_lower for kw in _TEAM_KEYWORDS)
        effective_k = self.k + (12 if is_team_query else 6) if is_strategic else self.k

        # Phase 0: summary document matching per domande analitiche
        summary_docs = self._find_summaries(original_question, generation)

        # Per domande strategiche senza summary match, inietta il roster BST
        if is_strategic and not summary_docs:
            summary_docs = self._find_summaries_by_category(
                "bst_ranking_non_legendary", generation,
            )

        # Per domande strategiche, inietta anche i dati dei capipalestra/E4
        trainer_docs: list[Document] = []
        if is_strategic:
            trainer_docs = self._find_trainer_docs(generation)

        # Inietta game_info docs (starters, esclusivi, leggendari) se rilevanti
        # Quando l'utente menziona un gioco specifico ("Pokemon Platino"),
        # filtra i game_info docs per quel gioco anziche' restituire tutti
        # quelli della generazione.
        game_info_docs: list[Document] = []
        game_slug: str | None = None
        if any(kw in original_question.lower() for kw in _GAME_INFO_KEYWORDS):
            game_slug = detect_game_slug(original_question)
            game_info_docs = self._find_game_info_docs(
                generation, original_question, game_slug=game_slug,
            )
            trainer_docs = trainer_docs + game_info_docs

        # When game-specific docs are found, remove overlapping summary
        # docs to prevent the generic gen-wide list from overriding
        # game-specific data.  E.g. "leggendari in Platino" should show
        # only Platino legendaries, not ALL gen-4 legendaries.
        if game_slug and game_info_docs:
            _INFO_TO_SUMMARY = {"legendaries": "legendary_mythical_list"}
            info_cats = {d.metadata.get("info_category") for d in game_info_docs}
            drop = {_INFO_TO_SUMMARY[c] for c in info_cats if c in _INFO_TO_SUMMARY}
            if drop:
                summary_docs = [
                    d for d in summary_docs
                    if d.metadata.get("summary_category") not in drop
                ]
                logger.info(
                    "Dropped summary categories %s (game-specific docs for %s)",
                    drop, game_slug,
                )

        # Phase 0.5: cross-generational availability docs (generation: 0)
        # Per query come "in quali giochi posso catturare Dratini", recupera
        # i documenti aggregati che coprono tutte le generazioni.
        availability_docs: list[Document] = self._find_availability_docs(
            original_question, retrieval_query=retrieval_query,
        )

        # Phase 1: exact name matching sui metadata
        # Usa sia la domanda originale che la retrieval_query arricchita
        # per catturare nomi da follow-up (es. "che debolezze ha?" + history)
        exact_docs = self._find_by_name(
            original_question, generation, retrieval_query=retrieval_query,
        )

        # Phase 1.5: Auto-retrieval build docs per query team
        # Quando l'utente chiede una squadra senza nominare Pokemon specifici,
        # estrae i nomi dai doc game_info (best_team) e summary (team_roster)
        # e recupera i build docs corrispondenti per fornire al LLM
        # stats e mosse consigliate per ogni Pokemon raccomandato.
        team_build_docs: list[Document] = []
        if is_team_query and not exact_docs:
            team_pokemon_names: list[str] = []
            # Priorita': best_team (game-specific), poi team_roster (gen-wide)
            for doc in game_info_docs:
                if doc.metadata.get("info_category") == "best_team":
                    team_pokemon_names.extend(
                        _extract_team_pokemon_names(doc.page_content),
                    )
            if not team_pokemon_names:
                for doc in summary_docs:
                    if doc.metadata.get("summary_category") == "team_roster_by_role":
                        team_pokemon_names.extend(
                            _extract_team_pokemon_names(doc.page_content),
                        )

            if team_pokemon_names:
                collection = self.vectorstore._collection
                seen_build_ids: set[str] = set()
                # Limita a max 6 build docs (una squadra tipica)
                for name in team_pokemon_names[:8]:
                    if len(team_build_docs) >= 6:
                        break
                    try:
                        results = collection.get(
                            where={
                                "$and": [
                                    {"generation": generation},
                                    {"entity_type": "build"},
                                    {"$or": [
                                        {"name_it": name},
                                        {"name_en": name},
                                    ]},
                                ],
                            },
                            include=["documents", "metadatas"],
                        )
                    except Exception:
                        logger.warning(
                            "Build doc fetch failed for %r", name,
                            exc_info=True,
                        )
                        continue
                    for j, doc_id in enumerate(results["ids"]):
                        if doc_id not in seen_build_ids:
                            seen_build_ids.add(doc_id)
                            team_build_docs.append(Document(
                                page_content=results["documents"][j],
                                metadata=results["metadatas"][j],
                            ))
                if team_build_docs:
                    logger.info(
                        "Team auto-retrieval: found %d build docs for %r",
                        len(team_build_docs),
                        [d.metadata.get("name_it") for d in team_build_docs],
                    )

        # Combina summary + availability + trainer + name match + team build
        pre_contents = {s.page_content for s in summary_docs}
        pre_docs = summary_docs + [
            d for d in availability_docs
            if d.page_content not in pre_contents
        ]
        pre_contents.update(d.page_content for d in availability_docs)
        pre_docs += [
            d for d in trainer_docs
            if d.page_content not in pre_contents
        ]
        pre_contents.update(d.page_content for d in trainer_docs)
        pre_docs += [
            d for d in exact_docs
            if d.page_content not in pre_contents
        ]
        pre_contents.update(d.page_content for d in exact_docs)
        pre_docs += [
            d for d in team_build_docs
            if d.page_content not in pre_contents
        ]

        # Phase 2: semantic search per contesto aggiuntivo
        remaining_k = max(effective_k - len(pre_docs), 3)
        excluded = _detect_excluded_types(original_question)

        if excluded:
            conditions: list[dict] = [{"generation": generation}]
            for etype in excluded:
                conditions.append({"entity_type": {"$ne": etype}})
            chroma_filter = {"$and": conditions}
        else:
            chroma_filter = {"generation": generation}

        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": remaining_k,
                "filter": chroma_filter,
            },
        )
        semantic_docs = retriever.invoke(retrieval_query)

        # Combina: summary + trainer + name match prima, poi semantic (senza duplicati)
        # Deduplica per chiave composita: usa campi diversi in base al tipo di doc
        def _doc_key(d: Document) -> tuple:
            etype = d.metadata.get("entity_type", "")
            gen = d.metadata.get("generation", "")
            # Ogni entity_type ha un identificatore univoco diverso
            if etype == "trainer_info":
                return (etype, d.metadata.get("game_slug", ""), gen)
            if etype == "game_info":
                return (etype, d.metadata.get("info_category", ""), d.metadata.get("game_slug", ""), gen)
            if etype == "summary":
                return (etype, d.metadata.get("summary_category", ""), gen)
            return (etype, d.metadata.get("name_en", ""), gen)

        seen_keys: set[tuple] = set()
        for d in pre_docs:
            seen_keys.add(_doc_key(d))

        for doc in semantic_docs:
            key = _doc_key(doc)
            if key not in seen_keys:
                seen_keys.add(key)
                pre_docs.append(doc)

        final_docs = pre_docs[:effective_k]

        logger.info(
            "Query: %r | Gen: %d | Strategic: %s | Team: %s | Excluded: %s | Summary: %d | Availability: %d | Trainer: %d | NameMatch: %d | TeamBuild: %d | Semantic: %d | Final: %d | Types: %s",
            retrieval_query[:80],
            generation,
            is_strategic,
            is_team_query,
            excluded,
            len(summary_docs),
            len(availability_docs),
            len(trainer_docs),
            len(exact_docs),
            len(team_build_docs),
            len(semantic_docs),
            len(final_docs),
            [d.metadata.get("entity_type", "?") for d in final_docs],
        )
        return final_docs

    @staticmethod
    def _detect_generation_with_history(
        question: str,
        chat_history: list[dict],
    ) -> int:
        """Rileva la generazione target dalla domanda o dalla chat history.

        Ordine di priorita:
        1. Domanda corrente (es. "che mosse ha in Pokemon Nero?" -> gen 5)
        2. Chat history - messaggi utente piu' recenti prima
           (es. precedente "Parlami di Dragonite in Pokemon Nero" -> gen 5)
        3. Fallback: ultima generazione (gen 9)

        Questo risolve il bug dei follow-up: se l'utente chiede
        "e le sue mosse?" dopo aver parlato di gen 5, la generazione
        viene propagata dalla history.
        """
        gen = detect_generation(question)
        if gen is not None:
            return gen

        # Cerca nei messaggi utente della history (dal piu' recente)
        for msg in reversed(chat_history):
            if msg["role"] == "user":
                gen = detect_generation(msg["content"])
                if gen is not None:
                    return gen

        return LATEST_GENERATION

    def invoke(
        self,
        question: str,
        chat_history: list[dict] | None = None,
    ) -> str:
        history_list = chat_history or []
        generation = self._detect_generation_with_history(question, history_list)
        is_strategic = _is_strategic_query(question)
        retrieval_query = self._build_retrieval_query(question, history_list)
        docs = self._retrieve(
            retrieval_query, generation,
            original_question=question, is_strategic=is_strategic,
        )
        context = _format_docs(docs)
        history = _convert_chat_history(history_list)

        selected_prompt = self.strategic_prompt if is_strategic else self.prompt
        chain = selected_prompt | self.llm | self.output_parser
        return chain.invoke({
            "question": question,
            "context": context,
            "generation": generation,
            "chat_history": history,
        })

    async def ainvoke(
        self,
        question: str,
        chat_history: list[dict] | None = None,
    ) -> str:
        history_list = chat_history or []
        generation = self._detect_generation_with_history(question, history_list)
        is_strategic = _is_strategic_query(question)
        retrieval_query = self._build_retrieval_query(question, history_list)
        docs = self._retrieve(
            retrieval_query, generation,
            original_question=question, is_strategic=is_strategic,
        )
        context = _format_docs(docs)
        history = _convert_chat_history(history_list)

        selected_prompt = self.strategic_prompt if is_strategic else self.prompt
        chain = selected_prompt | self.llm | self.output_parser
        return await chain.ainvoke({
            "question": question,
            "context": context,
            "generation": generation,
            "chat_history": history,
        })

    async def astream(
        self,
        question: str,
        chat_history: list[dict] | None = None,
    ):
        history_list = chat_history or []
        generation = self._detect_generation_with_history(question, history_list)
        is_strategic = _is_strategic_query(question)
        retrieval_query = self._build_retrieval_query(question, history_list)
        docs = self._retrieve(
            retrieval_query, generation,
            original_question=question, is_strategic=is_strategic,
        )
        context = _format_docs(docs)
        history = _convert_chat_history(history_list)

        selected_prompt = self.strategic_prompt if is_strategic else self.prompt

        invoke_args = {
            "question": question,
            "context": context,
            "generation": generation,
            "chat_history": history,
        }

        # Try primary LLM, fallback on 429 / quota errors
        chain = selected_prompt | self.llm | self.output_parser
        try:
            async for chunk in chain.astream(invoke_args):
                yield chunk
            return
        except Exception as exc:
            if self.fallback_llm and ("429" in str(exc) or "quota" in str(exc).lower()):
                logger.warning("Primary LLM quota exceeded, falling back: %s", str(exc)[:120])
            else:
                raise

        # Fallback LLM
        fallback_chain = selected_prompt | self.fallback_llm | self.output_parser
        async for chunk in fallback_chain.astream(invoke_args):
            yield chunk

    async def astream_cached(
        self,
        question: str,
        chat_history: list[dict] | None = None,
        cache: ResponseCache | None = None,
        metadata: dict | None = None,
    ):
        """Stream with cache support.

        On cache hit: yields the cached response in a single chunk.
        On cache miss: streams from LLM, collects the full response,
        and stores it in cache.

        Populates the *metadata* dict (if provided) with:
        - ``cache_hit``: bool
        - ``entry_id``: int | None
        - ``was_missing``: bool

        Cache eligibility:
        - ONLY the first question of a chat is cacheable (no prior
          assistant messages in history).
        - Follow-up questions are never cached because their meaning
          depends on the conversation context.

        NOTE: history_list may contain the current user message itself
        (sent by the frontend). We check for prior *assistant* messages
        to determine if there's actual conversation context.
        """
        meta = metadata if metadata is not None else {}
        meta.setdefault("cache_hit", False)
        meta.setdefault("entry_id", None)
        meta.setdefault("was_missing", False)
        history_list = chat_history or []
        generation = self._detect_generation_with_history(question, history_list)

        # Only the first question of a conversation is cacheable.
        # Follow-ups always depend on context and cannot be cached.
        has_prior_context = any(m["role"] == "assistant" for m in history_list)
        is_cacheable = not has_prior_context

        # Game-specific queries (e.g. "leggendari platino") are NOT cacheable
        # because the hash normalization strips game titles, causing false
        # positives between different games in the same generation
        # (e.g. "leggendari platino" ≠ "leggendari diamante").
        if is_cacheable:
            _game_slug = detect_game_slug(question)
            if _game_slug and any(kw in question.lower() for kw in _GAME_INFO_KEYWORDS):
                is_cacheable = False

        if cache and is_cacheable:
            cached = await cache.get(question, generation)
            if cached is not None:
                response_text, entry_id = cached
                meta["cache_hit"] = True
                meta["entry_id"] = entry_id
                yield response_text
                return

        # Cache miss (or non-cacheable follow-up) — stream from LLM
        full_response: list[str] = []
        async for chunk in self.astream(question, chat_history):
            full_response.append(chunk)
            yield chunk

        # Store cacheable questions
        response_text = "".join(full_response)
        if cache and is_cacheable and response_text.strip():
            # Auto-detect "missing info" responses → feedback='M'
            is_missing = _MISSING_PHRASE in response_text.lower()
            feedback = "M" if is_missing else "-"
            meta["was_missing"] = is_missing
            entry_id = await cache.put(question, generation, response_text, feedback=feedback)
            meta["entry_id"] = entry_id
