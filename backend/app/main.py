import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.core.cache import ResponseCache, load_custom_stopwords
from app.core.embeddings import get_embeddings
from app.db.database import Database
from app.core.llm import get_llm
from app.core.rag_chain import RAGChain
from app.core.vectorstore import get_vectorstore

# Configura logging — mostra INFO per i moduli app, WARNING per librerie rumorose
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log = logging.getLogger(__name__)
    settings = get_settings()

    # Initialize embeddings + vector store
    embeddings = get_embeddings(
        settings.embedding_provider,
        model=settings.embedding_model,
    )

    try:
        vectorstore = get_vectorstore(
            settings.chroma_persist_dir,
            settings.chroma_collection_name,
            embeddings,
        )
        doc_count = vectorstore._collection.count()
        log.info(
            "Vectorstore loaded: %d documents in '%s'",
            doc_count, settings.chroma_collection_name,
        )
    except Exception:
        log.exception("Failed to load vectorstore — starting with empty store")
        # Delete corrupted collection and create a fresh one
        import chromadb
        try:
            client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
            client.delete_collection(name=settings.chroma_collection_name)
            log.info("Deleted corrupted collection '%s'", settings.chroma_collection_name)
        except Exception:
            pass
        vectorstore = get_vectorstore(
            settings.chroma_persist_dir,
            settings.chroma_collection_name,
            embeddings,
        )
        log.info("Created empty vectorstore — run /api/admin/ingest to populate")

    # Initialize LLM (primary + fallback)
    llm = get_llm(
        settings.llm_provider,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
    )
    fallback_llm = None
    if settings.llm_fallback_model and settings.llm_fallback_model != settings.llm_model:
        fallback_llm = get_llm(
            settings.llm_provider,
            model=settings.llm_fallback_model,
            temperature=settings.llm_temperature,
        )
        log.info(
            "LLM fallback: %s → %s",
            settings.llm_model, settings.llm_fallback_model,
        )

    # Build RAG chain
    app.state.vectorstore = vectorstore
    app.state.rag_chain = RAGChain(
        llm=llm,
        vectorstore=vectorstore,
        k=settings.retriever_k,
        fallback_llm=fallback_llm,
    )

    # Initialize user database
    db = Database(settings.db_path)
    await db.connect()
    app.state.db = db
    app.state.jwt_secret = settings.jwt_secret

    # Initialize response cache (shares the same SQLite connection)
    app.state.cache = ResponseCache(db._conn)

    # Load custom stopwords from DB into the hash pipeline
    await load_custom_stopwords(db._conn)

    yield

    # Cleanup
    await db.close()


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
