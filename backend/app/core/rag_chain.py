import logging
import re

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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

# Stop words italiane da ignorare nell'estrazione nomi entita
_STOP_WORDS = frozenset({
    "che", "chi", "per", "con", "del", "della", "delle", "dei", "degli",
    "nel", "nella", "nelle", "nei", "negli", "sul", "sulla", "sulle",
    "come", "cosa", "quali", "quale", "sono", "una", "uno", "gli", "non",
    "parlami", "dimmi", "mostrami", "spiegami", "descrivi", "elenca",
    "Pokemon", "pokemon", "pokémon",
    "tipo", "tipi", "mossa", "mosse", "abilita", "stat", "statistiche",
    "debolezze", "debolezza", "resistenze", "resistenza",
    "generazione", "gen",
})


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

        La domanda corrente viene messa PRIMA del contesto per dare piu'
        peso semantico all'embedding della query attuale.
        """
        if not chat_history or len(question) > 40:
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
    ) -> list[Document]:
        """Cerca documenti il cui nome (IT o EN) matcha parole nella domanda.

        Risolve il problema dell'embedding dilution: i documenti Pokemon
        sono troppo lunghi (~1400 chars) per il modello di embedding
        (max 128 token), quindi il nome si perde nell'embedding.
        Il matching diretto sui metadata bypassa completamente il problema.
        """
        candidates = _extract_candidate_names(question)
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
        exact_docs = self._find_by_name(original_question, generation)

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
        exact_ids = {id(d) for d in exact_docs}
        exact_content_keys = set()
        for d in exact_docs:
            key = (
                d.metadata.get("entity_type", ""),
                d.metadata.get("name_en", ""),
                d.metadata.get("generation", ""),
            )
            exact_content_keys.add(key)

        for doc in semantic_docs:
            key = (
                doc.metadata.get("entity_type", ""),
                doc.metadata.get("name_en", ""),
                doc.metadata.get("generation", ""),
            )
            if key not in exact_content_keys:
                exact_docs.append(doc)

        final_docs = exact_docs[:self.k]

        logger.info(
            "Query: %r | Gen: %d | Excluded: %s | NameMatch: %d | Semantic: %d | Final: %d | Types: %s",
            retrieval_query[:80],
            generation,
            excluded,
            len([d for d in final_docs
                 if (d.metadata.get("entity_type", ""), d.metadata.get("name_en", ""), d.metadata.get("generation", ""))
                 in exact_content_keys]),
            len(semantic_docs),
            len(final_docs),
            [d.metadata.get("entity_type", "?") for d in final_docs],
        )
        return final_docs

    def invoke(
        self,
        question: str,
        chat_history: list[dict] | None = None,
    ) -> str:
        generation = detect_generation(question) or LATEST_GENERATION
        retrieval_query = self._build_retrieval_query(question, chat_history or [])
        docs = self._retrieve(retrieval_query, generation, original_question=question)
        context = _format_docs(docs)
        history = _convert_chat_history(chat_history or [])

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
        generation = detect_generation(question) or LATEST_GENERATION
        retrieval_query = self._build_retrieval_query(question, chat_history or [])
        docs = self._retrieve(retrieval_query, generation, original_question=question)
        context = _format_docs(docs)
        history = _convert_chat_history(chat_history or [])

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
        generation = detect_generation(question) or LATEST_GENERATION
        retrieval_query = self._build_retrieval_query(question, chat_history or [])
        docs = self._retrieve(retrieval_query, generation, original_question=question)
        context = _format_docs(docs)
        history = _convert_chat_history(chat_history or [])

        chain = self.prompt | self.llm | self.output_parser
        async for chunk in chain.astream({
            "question": question,
            "context": context,
            "generation": generation,
            "chat_history": history,
        }):
            yield chunk
