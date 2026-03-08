"""Admin endpoints — ingestion trigger (protected by JWT_SECRET)."""

import asyncio

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/ingest")
async def trigger_ingestion(
    request: Request,
    secret: str = Query(..., description="JWT_SECRET as auth"),
    force: bool = Query(False),
):
    """Run data ingestion. Call once after first deploy.

    Usage:
        POST /api/admin/ingest?secret=YOUR_JWT_SECRET&force=false
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # Run ingestion in background so the request doesn't timeout
    from app.config import get_settings
    from app.core.embeddings import get_embeddings
    from app.core.generation_mapper import MAX_POKEMON_PER_GEN
    from app.ingestion.fetcher import fetch_all_data
    from app.ingestion.indexer import index_documents
    from app.ingestion.pokeapi_client import PokeAPIClient
    from app.ingestion.transformers import build_all_documents_for_generation

    settings = get_settings()
    persist_dir = settings.chroma_persist_dir

    # Quick check: already indexed?
    if not force:
        from pathlib import Path

        if Path(persist_dir).exists():
            from langchain_chroma import Chroma

            embeddings = get_embeddings(
                settings.embedding_provider, model=settings.embedding_model
            )
            existing = Chroma(
                persist_directory=persist_dir,
                collection_name=settings.chroma_collection_name,
                embedding_function=embeddings,
            )
            count = existing._collection.count()
            if count > 0:
                return {
                    "status": "skipped",
                    "message": f"ChromaDB already has {count} documents. Use force=true to re-index.",
                }

    # Run ingestion (this takes 10-15 minutes)
    async with PokeAPIClient(cache_dir="data/raw") as client:
        all_data = await fetch_all_data(client, 1025)

    all_docs = []
    generations = list(range(1, 10))
    for gen in generations:
        if gen not in MAX_POKEMON_PER_GEN:
            continue
        docs = build_all_documents_for_generation(all_data, gen)
        all_docs.extend(docs)

    embeddings = get_embeddings(
        settings.embedding_provider, model=settings.embedding_model
    )
    use_api_delay = settings.embedding_provider in ("gemini", "openai")
    index_documents(
        documents=all_docs,
        embeddings=embeddings,
        persist_dir=persist_dir,
        collection_name=settings.chroma_collection_name,
        use_api_delay=use_api_delay,
    )

    return {
        "status": "completed",
        "documents_indexed": len(all_docs),
    }
