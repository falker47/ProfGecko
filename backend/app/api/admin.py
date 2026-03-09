"""Admin endpoints — ingestion + cache management (protected by JWT_SECRET)."""

import csv
import io
from pathlib import Path as FilePath

from fastapi import APIRouter, Body, File, HTTPException, Path, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.cache import ResponseCache


class UpdateEntryBody(BaseModel):
    response: str | None = None
    generation: int | None = None


class AddStopwordsBody(BaseModel):
    words: list[str]

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

    # Reload the in-memory vectorstore + RAG chain so the server uses the
    # freshly indexed data without needing a restart.
    from app.core.vectorstore import get_vectorstore
    from app.core.llm import get_llm
    from app.core.rag_chain import RAGChain

    new_vs = get_vectorstore(persist_dir, settings.chroma_collection_name, embeddings)
    request.app.state.vectorstore = new_vs

    llm = get_llm(settings.llm_provider, model=settings.llm_model, temperature=settings.llm_temperature)
    fallback_llm = None
    if settings.llm_fallback_model and settings.llm_fallback_model != settings.llm_model:
        fallback_llm = get_llm(settings.llm_provider, model=settings.llm_fallback_model, temperature=settings.llm_temperature)

    request.app.state.rag_chain = RAGChain(
        llm=llm, vectorstore=new_vs, k=settings.retriever_k, fallback_llm=fallback_llm,
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


@router.get("/cache/entries")
async def cache_list_entries(
    request: Request,
    secret: str = Query(..., description="JWT_SECRET as auth"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    reviewed: bool | None = Query(None, description="Filter: true=reviewed, false=not reviewed, omit=all"),
    generation: int | None = Query(None, ge=1, le=9),
    search: str | None = Query(None, description="Search in question text"),
    feedback: str | None = Query(None, description="Filter by feedback: V, F, M, or -"),
    sort_by: str = Query("id", description="Column to sort by: id, generation, created_at, hit_count"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
):
    """List cache entries with pagination, filters and sorting.

    Usage:
        GET /api/admin/cache/entries?secret=...&page=1&sort_by=hit_count&sort_order=desc
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    cache = _get_cache(request)
    return await cache.list_entries(
        page=page,
        per_page=per_page,
        reviewed_only=reviewed,
        generation=generation,
        search=search,
        feedback=feedback,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.put("/cache/entries/{entry_id}")
async def cache_update_entry(
    request: Request,
    entry_id: int = Path(..., description="Cache entry ID"),
    secret: str = Query(..., description="JWT_SECRET as auth"),
    body: UpdateEntryBody = Body(...),
):
    """Update a cache entry's response and/or generation, mark as reviewed.

    Usage:
        PUT /api/admin/cache/entries/42?secret=...
        Body: {"response": "New text"}  or  {"generation": 1}  or both
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    if body.response is None and body.generation is None:
        raise HTTPException(status_code=400, detail="Provide response and/or generation")

    cache = _get_cache(request)
    result = await cache.update_entry(
        entry_id, response=body.response, generation=body.generation,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return result


@router.post("/cache/entries/{entry_id}/approve")
async def cache_approve_entry(
    request: Request,
    entry_id: int = Path(..., description="Cache entry ID"),
    secret: str = Query(..., description="JWT_SECRET as auth"),
):
    """Mark a cache entry as reviewed without changing the response.

    Usage:
        POST /api/admin/cache/entries/42/approve?secret=...
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    cache = _get_cache(request)
    success = await cache.mark_reviewed(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "ok", "entry_id": entry_id, "reviewed": True}


@router.delete("/cache/entries/{entry_id}")
async def cache_delete_entry(
    request: Request,
    entry_id: int = Path(..., description="Cache entry ID"),
    secret: str = Query(..., description="JWT_SECRET as auth"),
):
    """Delete a single cache entry.

    Usage:
        DELETE /api/admin/cache/entries/42?secret=...
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    cache = _get_cache(request)
    success = await cache.delete_entry(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "ok", "entry_id": entry_id}


@router.post("/cache/rehash")
async def cache_rehash(
    request: Request,
    secret: str = Query(..., description="JWT_SECRET as auth"),
):
    """Recompute all hashes after normalization rule changes.

    Run this after deploying new stopwords/synonyms to ensure
    existing entries match queries hashed with the updated rules.

    Usage:
        POST /api/admin/cache/rehash?secret=YOUR_JWT_SECRET
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    cache = _get_cache(request)
    result = await cache.rehash_all()
    return {
        "status": "ok",
        "entries_updated": result["updated"],
        "duplicates_found": result["duplicates_found"],
        "duplicates": result["duplicates"],
    }


@router.get("/cache/stopwords")
async def list_stopwords(
    request: Request,
    secret: str = Query(..., description="JWT_SECRET as auth"),
):
    """List all custom stopwords.

    Usage:
        GET /api/admin/cache/stopwords?secret=YOUR_JWT_SECRET
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    cache = _get_cache(request)
    words = await cache.list_stopwords()
    return {"words": words, "total": len(words)}


@router.post("/cache/stopwords")
async def add_stopwords(
    request: Request,
    secret: str = Query(..., description="JWT_SECRET as auth"),
    body: AddStopwordsBody = Body(...),
):
    """Add custom stopwords and rehash all entries.

    Usage:
        POST /api/admin/cache/stopwords?secret=YOUR_JWT_SECRET
        Body: {"words": ["dammi", "fammi"]}
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    if not body.words:
        raise HTTPException(status_code=400, detail="Provide at least one word")

    cache = _get_cache(request)
    result = await cache.add_stopwords(body.words)

    # Auto-rehash so all stored hashes reflect the new stopwords
    rehash_result = await cache.rehash_all()

    return {
        "status": "ok",
        "stopwords_added": result["added"],
        "stopwords_total": result["total"],
        "entries_rehashed": rehash_result["updated"],
        "duplicates_found": rehash_result["duplicates_found"],
    }


@router.delete("/cache/stopwords/{word}")
async def remove_stopword(
    request: Request,
    word: str = Path(..., description="Stopword to remove"),
    secret: str = Query(..., description="JWT_SECRET as auth"),
):
    """Remove a custom stopword and rehash all entries.

    Usage:
        DELETE /api/admin/cache/stopwords/dammi?secret=YOUR_JWT_SECRET
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    cache = _get_cache(request)
    removed = await cache.remove_stopword(word)
    if not removed:
        raise HTTPException(status_code=404, detail="Stopword not found")

    # Auto-rehash so all stored hashes reflect the removal
    rehash_result = await cache.rehash_all()

    return {
        "status": "ok",
        "word_removed": word,
        "entries_rehashed": rehash_result["updated"],
    }


@router.get("/cache/debug")
async def cache_debug_hash(
    request: Request,
    secret: str = Query(..., description="JWT_SECRET as auth"),
    question: str = Query(..., description="Question to analyze"),
    generation: int = Query(9, ge=1, le=9, description="Generation (default 9)"),
):
    """Show how a question would be hashed — no DB writes.

    Use this to verify that two different phrasings produce the same
    normal_hash before testing them in the chatbot.

    Usage:
        GET /api/admin/cache/debug?secret=...&question=debolezze garchomp gen 5&generation=5
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    return ResponseCache.debug_hash(question, generation)


@router.post("/cache/import")
async def cache_import_csv(
    request: Request,
    secret: str = Query(..., description="JWT_SECRET as auth"),
    file: UploadFile = File(..., description="CSV file with columns: question, generation, response"),
    skip_duplicates: bool = Query(True, description="Skip entries whose normalized hash already exists"),
):
    """Bulk-import cache entries from a CSV file.

    The CSV must have at least these columns: question, generation, response.
    Other columns are ignored. Entries are stored with reviewed=0.

    Usage:
        POST /api/admin/cache/import?secret=YOUR_JWT_SECRET
        Content-Type: multipart/form-data
        Body: file=@seed_cache.csv
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    content = await file.read()
    # Try UTF-8 BOM first, then UTF-8
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("utf-8")

    reader = csv.DictReader(io.StringIO(text))

    # Validate required columns
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV is empty or has no headers")
    required = {"question", "generation", "response"}
    missing = required - set(reader.fieldnames)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing required columns: {', '.join(sorted(missing))}",
        )

    rows = list(reader)
    if not rows:
        raise HTTPException(status_code=400, detail="CSV has no data rows")

    cache = _get_cache(request)
    result = await cache.import_entries(rows, skip_duplicates=skip_duplicates)
    return {
        "status": "ok",
        "imported": result["imported"],
        "skipped": result["skipped"],
        "total_in_file": len(rows),
    }


@router.get("/cache/export")
async def cache_export_csv(
    request: Request,
    secret: str = Query(..., description="JWT_SECRET as auth"),
):
    """Export all cache entries as a CSV file (opens in Excel / Google Sheets).

    Usage:
        GET /api/admin/cache/export?secret=YOUR_JWT_SECRET
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    cache = _get_cache(request)
    rows = await cache.export_all()

    # Build CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "question", "generation", "response",
        "hit_count", "reviewed", "feedback", "exact_hash", "normal_hash",
        "created_at", "last_hit_at", "reviewed_at",
    ])
    for row in rows:
        writer.writerow([
            row["id"], row["question"], row["generation"], row["response"],
            row["hit_count"], row["reviewed"], row["feedback"], row["exact_hash"],
            row["normal_hash"], row["created_at"], row["last_hit_at"],
            row["reviewed_at"],
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")  # BOM for Excel
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cache_entries.csv"},
    )


@router.get("/db/download")
async def download_database(
    request: Request,
    secret: str = Query(..., description="JWT_SECRET as auth"),
):
    """Download the full SQLite database file.

    Open it with DB Browser for SQLite (https://sqlitebrowser.org/).

    Usage:
        GET /api/admin/db/download?secret=YOUR_JWT_SECRET
    """
    if secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    from app.config import get_settings

    db_path = FilePath(get_settings().db_path)
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="Database file not found")

    return StreamingResponse(
        open(db_path, "rb"),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={db_path.name}",
        },
    )
