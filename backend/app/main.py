from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.core.embeddings import get_embeddings
from app.core.llm import get_llm
from app.core.rag_chain import RAGChain
from app.core.vectorstore import get_vectorstore


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Initialize embeddings + vector store
    embeddings = get_embeddings(
        settings.embedding_provider,
        model=settings.embedding_model,
    )
    vectorstore = get_vectorstore(
        settings.chroma_persist_dir,
        settings.chroma_collection_name,
        embeddings,
    )

    # Initialize LLM
    llm = get_llm(
        settings.llm_provider,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )

    # Build RAG chain
    app.state.vectorstore = vectorstore
    app.state.rag_chain = RAGChain(
        llm=llm,
        vectorstore=vectorstore,
        k=settings.retriever_k,
    )

    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Prof. Gallade API",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
