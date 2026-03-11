import logging
import re

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.cache import ResponseCache
from app.core.generation_mapper import LATEST_GENERATION, detect_generation, detect_game_slug
from app.core.prompts import PROF_GALLADE_SYSTEM_PROMPT, PROF_GALLADE_STRATEGIC_PROMPT

logger = logging.getLogger(__name__)

# --- Entity-type intent detection ---
# Items e nature vengono esclusi dal retrieval di default perche'
# sommergono i risultati per le query su Pokemon/mosse/tipi/abilita'.
# Vengono inclusi solo quando l'utente li chiede esplicitamente.

_ITEM_KEYWORDS = frozenset({
    "strumento", "strumenti", "oggetto", "oggetti",
    "bacca", "bacche", "item", "items", "berry", "berries",
    "pietra", "held item",
})
_NATURE_KEYWORDS = frozenset({
    "natura", "nature", "natures", "indole",
})

# Keywords that trigger game_info document injection
_GAME_INFO_KEYWORDS = frozenset({
    "starter", "iniziale", "iniziali", "quale scegliere",
    "squadra", "team", "pokemon da usare",
    "esclusivo", "esclusivi", "esclusiva", "exclusive",
    "solo in", "differenze versione",
    "leggendario", "leggendari", "mitico", "mitici",
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
    "strategia", "competitivo", "counter", "contrastare",
    "avventura", "conviene", "alternativa", "alternative",
    "vantaggi", "svantaggi",
    # Trainer / gym terms
    "capopalestra", "capipalestra", "superquattro",
    "campione", "champion", "palestra", "lega",
    # Game info terms
    "starter", "iniziale", "iniziali", "esclusivo", "esclusivi",
    "leggendario", "leggendari",
    # Game title words (prevent game names from being name candidates)
    "rosso", "blu", "giallo", "oro", "argento", "cristallo",
    "rubino", "zaffiro", "smeraldo",
    "diamante", "perla", "platino",
    "nero", "bianco",
    "sole", "luna", "ultrasole", "ultraluna",
    "spada", "scudo",
    "scarlatto", "violetto",
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
    # Termini Pokemon generici
    "pokemon", "pokémon",
    "tipo", "tipi", "mossa", "mosse", "abilita", "abilità", "stat", "statistiche",
    "debolezze", "debolezza", "resistenze", "resistenza", "immunita", "immunità",
    "generazione", "gen", "catena", "evolutiva", "evoluzione",
    "base", "totale", "velocita", "velocità", "attacco", "difesa", "speciale",
    # Verbi/termini aggiuntivi
    "qual", "quale", "quando", "quanti", "quante",
    "tasso", "crescita", "cattura",
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
        ["squadra", "team", "roster", "composizione"],
        ["team_roster_by_role"],
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
    # Include Smogon sets when: explicit Smogon keywords OR strategic query
    if not any(kw in q for kw in _SMOGON_KEYWORDS) and not _is_strategic_query(q):
        excluded.append("smogon_set")
    return excluded


# --- Strategic query detection ---
_STRATEGIC_KEYWORDS: list[str] = [
    # Team building
    "squadra", "team", "roster", "composizione",
    # Build / moveset
    "build", "moveset", "miglior set",
    # Advice
    "consigliata", "consigliato", "consigli", "consiglio", "consiglia",
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
    "avventura", "playthrough", "completare",
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
            ("system", PROF_GALLADE_SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{question}"),
        ])

        self.strategic_prompt = ChatPromptTemplate.from_messages([
            ("system", PROF_GALLADE_STRATEGIC_PROMPT),
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
            return []
        docs = []
        for j, doc_id in enumerate(results["ids"]):
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
            return []
        docs = []
        for j, doc_id in enumerate(results["ids"]):
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
                     "quale scegliere", "chi scegliere")
        is_best = any(kw in q for kw in _best_kw)

        if any(kw in q for kw in ("starter", "iniziale", "iniziali")):
            categories.append("best_starter" if is_best else "starters")
        if any(kw in q for kw in ("squadra", "team", "pokemon da usare")):
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
            return []

        docs = []
        for j, doc_id in enumerate(results["ids"]):
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
        effective_k = self.k + 6 if is_strategic else self.k

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

        # Phase 1: exact name matching sui metadata
        # Usa sia la domanda originale che la retrieval_query arricchita
        # per catturare nomi da follow-up (es. "che debolezze ha?" + history)
        exact_docs = self._find_by_name(
            original_question, generation, retrieval_query=retrieval_query,
        )

        # Combina summary + trainer + name match (summary e trainer prima)
        pre_contents = {s.page_content for s in summary_docs}
        pre_docs = summary_docs + [
            d for d in trainer_docs
            if d.page_content not in pre_contents
        ]
        pre_contents.update(d.page_content for d in pre_docs)
        pre_docs += [
            d for d in exact_docs
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
            "Query: %r | Gen: %d | Strategic: %s | Excluded: %s | Summary: %d | Trainer: %d | NameMatch: %d | Semantic: %d | Final: %d | Types: %s",
            retrieval_query[:80],
            generation,
            is_strategic,
            excluded,
            len(summary_docs),
            len(trainer_docs),
            len(exact_docs),
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
    ):
        """Stream with cache support.

        On cache hit: yields the cached response in a single chunk
        and sets ``self._last_cache_hit = True``.
        On cache miss: streams from LLM, collects the full response,
        stores it in cache, and sets ``self._last_cache_hit = False``.

        Cache eligibility:
        - First question (no history): always cacheable.
        - Standalone question (>= 6 words) even with history: cacheable,
          because its meaning doesn't depend on previous messages.
        - Short follow-up (< 6 words, e.g. "e le mosse?"): NOT cacheable,
          because its meaning depends on the conversation context.

        Uses the same word-count threshold as _build_retrieval_query.
        """
        self._last_cache_hit = False
        self._last_entry_id: int | None = None
        self._last_was_missing = False
        history_list = chat_history or []
        generation = self._detect_generation_with_history(question, history_list)

        # A question is cacheable if it's the first in the conversation
        # OR if it's self-contained (>= 6 words, meaning doesn't depend
        # on chat history). Short follow-ups like "e le mosse?" are
        # context-dependent and cannot be meaningfully cached.
        #
        # NOTE: history_list may contain the current user message itself
        # (sent by the frontend). We check for prior *assistant* messages
        # to determine if there's actual conversation context.
        word_count = len(question.split())
        has_prior_context = any(m["role"] == "assistant" for m in history_list)
        is_cacheable = not has_prior_context or word_count >= _SELF_CONTAINED_WORD_COUNT

        # Game-specific game_info queries must bypass cache because the
        # cache normalizes away game titles (e.g. "platino"), making
        # "leggendari platino" hash-equal to "leggendari gen 4" despite
        # requiring different answers (game-specific vs gen-wide).
        if is_cacheable:
            _game_slug = detect_game_slug(question)
            if _game_slug and any(
                kw in question.lower() for kw in _GAME_INFO_KEYWORDS
            ):
                is_cacheable = False

        if cache and is_cacheable:
            cached = await cache.get(question, generation)
            if cached is not None:
                response_text, entry_id = cached
                self._last_cache_hit = True
                self._last_entry_id = entry_id
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
            self._last_was_missing = is_missing
            entry_id = await cache.put(question, generation, response_text, feedback=feedback)
            self._last_entry_id = entry_id
