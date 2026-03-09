import logging
import re

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.cache import ResponseCache
from app.core.generation_mapper import LATEST_GENERATION, detect_generation
from app.core.prompts import PROF_GALLADE_SYSTEM_PROMPT

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
    # Termini Pokemon generici
    "pokemon", "pokémon",
    "tipo", "tipi", "mossa", "mosse", "abilita", "stat", "statistiche",
    "debolezze", "debolezza", "resistenze", "resistenza", "immunita",
    "generazione", "gen", "catena", "evolutiva", "evoluzione",
    "base", "totale", "velocita", "attacco", "difesa", "speciale",
})

# Soglia parole per considerare una domanda auto-contenuta (non un follow-up).
# Domande con piu' parole di questa soglia non vengono arricchite con
# contesto dalla chat history per evitare cross-contamination.
_SELF_CONTAINED_WORD_COUNT = 6

# Phrase used by the LLM when context doesn't contain the answer.
# Matched (lowercase) against response text to auto-flag as feedback='M'.
_MISSING_PHRASE = "non ho questa informazione"


def _detect_excluded_types(question: str) -> list[str]:
    """Determina quali entity_type escludere dal retrieval ChromaDB.

    Di default esclude 'item' e 'nature'. Li include solo se la
    domanda contiene keyword specifiche (es. 'bacca', 'natura').
    """
    q = question.lower()
    excluded: list[str] = []
    if not any(kw in q for kw in _ITEM_KEYWORDS):
        excluded.append("item")
    if not any(kw in q for kw in _NATURE_KEYWORDS):
        excluded.append("nature")
    return excluded


def _extract_candidate_names(question: str) -> list[str]:
    """Estrae parole candidate come nomi di entita dalla domanda.

    Ritorna parole di almeno 3 caratteri, rimuovendo stop words e
    punteggiatura. Usato per il matching diretto sui metadata ChromaDB.
    """
    words = re.findall(r"[a-zA-ZÀ-ÿ\-]+", question.lower())
    return [
        w for w in words
        if len(w) >= 3 and w not in _STOP_WORDS
    ]


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

    def __init__(self, llm: BaseChatModel, vectorstore: Chroma, k: int = 5):
        self.llm = llm
        self.vectorstore = vectorstore
        self.k = k

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", PROF_GALLADE_SYSTEM_PROMPT),
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

    def _retrieve(
        self,
        retrieval_query: str,
        generation: int,
        original_question: str,
    ) -> list[Document]:
        """Recupera documenti con strategia ibrida: name match + semantic search.

        1. Name matching: cerca entita il cui nome appare nella domanda
           (risolve l'embedding dilution dei documenti lunghi)
        2. Semantic search: riempie i posti rimanenti con risultati
           semanticamente rilevanti (cattura contesto aggiuntivo)
        """
        # Phase 1: exact name matching sui metadata
        # Usa sia la domanda originale che la retrieval_query arricchita
        # per catturare nomi da follow-up (es. "che debolezze ha?" + history)
        exact_docs = self._find_by_name(
            original_question, generation, retrieval_query=retrieval_query,
        )

        # Phase 2: semantic search per contesto aggiuntivo
        remaining_k = max(self.k - len(exact_docs), 3)
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

        # Combina: exact match prima, poi semantic (senza duplicati)
        # Deduplica per chiave (entity_type, name_en, generation)
        seen_keys: set[tuple] = set()
        for d in exact_docs:
            key = (
                d.metadata.get("entity_type", ""),
                d.metadata.get("name_en", ""),
                d.metadata.get("generation", ""),
            )
            seen_keys.add(key)

        for doc in semantic_docs:
            key = (
                doc.metadata.get("entity_type", ""),
                doc.metadata.get("name_en", ""),
                doc.metadata.get("generation", ""),
            )
            if key not in seen_keys:
                seen_keys.add(key)
                exact_docs.append(doc)

        final_docs = exact_docs[:self.k]

        logger.info(
            "Query: %r | Gen: %d | Excluded: %s | NameMatch: %d | Semantic: %d | Final: %d | Types: %s",
            retrieval_query[:80],
            generation,
            excluded,
            len([d for d in final_docs
                 if (d.metadata.get("entity_type", ""), d.metadata.get("name_en", ""), d.metadata.get("generation", ""))
                 in seen_keys]),
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
        retrieval_query = self._build_retrieval_query(question, history_list)
        docs = self._retrieve(retrieval_query, generation, original_question=question)
        context = _format_docs(docs)
        history = _convert_chat_history(history_list)

        chain = self.prompt | self.llm | self.output_parser
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
        retrieval_query = self._build_retrieval_query(question, history_list)
        docs = self._retrieve(retrieval_query, generation, original_question=question)
        context = _format_docs(docs)
        history = _convert_chat_history(history_list)

        chain = self.prompt | self.llm | self.output_parser
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
        retrieval_query = self._build_retrieval_query(question, history_list)
        docs = self._retrieve(retrieval_query, generation, original_question=question)
        context = _format_docs(docs)
        history = _convert_chat_history(history_list)

        chain = self.prompt | self.llm | self.output_parser
        async for chunk in chain.astream({
            "question": question,
            "context": context,
            "generation": generation,
            "chat_history": history,
        }):
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
        history_list = chat_history or []
        generation = self._detect_generation_with_history(question, history_list)

        # A question is cacheable if it's the first in the conversation
        # OR if it's self-contained (>= 6 words, meaning doesn't depend
        # on chat history). Short follow-ups like "e le mosse?" are
        # context-dependent and cannot be meaningfully cached.
        word_count = len(question.split())
        is_cacheable = not history_list or word_count >= _SELF_CONTAINED_WORD_COUNT

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
            feedback = "M" if _MISSING_PHRASE in response_text.lower() else "-"
            entry_id = await cache.put(question, generation, response_text, feedback=feedback)
            self._last_entry_id = entry_id
