import logging

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.generation_mapper import LATEST_GENERATION, detect_generation
from app.core.prompts import PROF_GALLADE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


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

    def _retrieve(self, question: str, generation: int) -> list[Document]:
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": self.k,
                "filter": {"generation": generation},
            },
        )
        docs = retriever.invoke(question)
        logger.info(
            "Query: %r | Gen detected: %d | Docs retrieved: %d | Types: %s",
            question[:80],
            generation,
            len(docs),
            [d.metadata.get("entity_type", "?") for d in docs],
        )
        return docs

    def invoke(
        self,
        question: str,
        chat_history: list[dict] | None = None,
    ) -> str:
        generation = detect_generation(question) or LATEST_GENERATION
        docs = self._retrieve(question, generation)
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
        docs = self._retrieve(question, generation)
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
        docs = self._retrieve(question, generation)
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
