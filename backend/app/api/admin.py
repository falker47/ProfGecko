"""Admin endpoints — ingestion + cache management (protected by JWT_SECRET)."""

from fastapi import APIRouter, HTTPException, Query, Request

from app.core.cache import ResponseCache

router = APIRouter(prefix="/admin", tags=["admin"])


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


def _get_cache(request: Request) -> ResponseCache:
    cache: ResponseCache | None = getattr(request.app.state, "cache", None)
    if cache is None:
        raise HTTPException(status_code=503, detail="Cache not initialized")
    return cache


@router.get("/cache/stats")
async def cache_stats(
    request: Request,
    secret: str = Query(..., description="JWT_SECRET as auth"),
):
    """Return cache statistics (total entries, total hits).

    Usage:
        GET /api/admin/cache/stats?secret=YOUR_JWT_SECRET
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    cache = _get_cache(request)
    return await cache.stats()


@router.post("/cache/invalidate")
async def cache_invalidate(
    request: Request,
    secret: str = Query(..., description="JWT_SECRET as auth"),
):
    """Clear the entire response cache.

    Usage:
        POST /api/admin/cache/invalidate?secret=YOUR_JWT_SECRET
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    cache = _get_cache(request)
    deleted = await cache.invalidate_all()
    return {"status": "ok", "entries_deleted": deleted}


@router.post("/cache/cleanup")
async def cache_cleanup(
    request: Request,
    secret: str = Query(..., description="JWT_SECRET as auth"),
    max_age_days: int = Query(90, description="Remove entries older than N days"),
):
    """Remove stale cache entries that haven't been hit recently.

    Usage:
        POST /api/admin/cache/cleanup?secret=YOUR_JWT_SECRET&max_age_days=90
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    cache = _get_cache(request)
    deleted = await cache.cleanup(max_age_days=max_age_days)
    return {"status": "ok", "stale_entries_removed": deleted}
