"""Admin endpoints — ingestion + cache management (protected by X-Admin-Secret header)."""

import asyncio
import csv
import io
import logging
import time
from pathlib import Path as FilePath

from fastapi import APIRouter, Body, Depends, File, HTTPException, Path, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth.dependencies import verify_admin_secret
from app.core.cache import ResponseCache

logger = logging.getLogger(__name__)

# --- Background ingestion state ---
_ingestion_status: str = "idle"  # idle | running | completed | error
_ingestion_result: dict | None = None
_ingestion_started_at: float | None = None


class UpdateEntryBody(BaseModel):
    response: str | None = None
    generation: int | None = None


class AddStopwordsBody(BaseModel):
    words: list[str]

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(verify_admin_secret)])


@router.get("/vectorstore/stats")
async def vectorstore_stats(request: Request):
    """Return vectorstore statistics (document count)."""
    vectorstore = getattr(request.app.state, "vectorstore", None)
    if vectorstore is None:
        raise HTTPException(status_code=503, detail="Vectorstore not initialized")

    doc_count = vectorstore._collection.count()
    return {"documents_count": doc_count}


@router.post("/reload-vectorstore")
async def reload_vectorstore(request: Request):
    """Reload the in-memory vectorstore from disk without re-ingesting.

    Use after running `run_ingestion.bat` (CLI ingestion) to pick up
    the freshly indexed documents without restarting the backend.
    """
    from app.config import get_settings
    from app.core.embeddings import get_embeddings
    from app.core.llm import get_llm
    from app.core.rag_chain import RAGChain
    from app.core.vectorstore import get_vectorstore

    settings = get_settings()

    embeddings = get_embeddings(
        settings.embedding_provider, model=settings.embedding_model,
    )
    new_vs = get_vectorstore(
        settings.chroma_persist_dir,
        settings.chroma_collection_name,
        embeddings,
    )
    doc_count = new_vs._collection.count()

    # Rebuild LLM + RAG chain with the fresh vectorstore
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

    request.app.state.vectorstore = new_vs
    request.app.state.rag_chain = RAGChain(
        llm=llm,
        vectorstore=new_vs,
        k=settings.retriever_k,
        fallback_llm=fallback_llm,
    )

    return {
        "status": "ok",
        "documents_loaded": doc_count,
    }


async def _run_ingestion_background(app_state, force: bool):
    """Background coroutine that performs the full ingestion pipeline."""
    global _ingestion_status, _ingestion_result, _ingestion_started_at

    try:
        from app.config import get_settings
        from app.core.embeddings import get_embeddings
        from app.core.generation_mapper import MAX_POKEMON_PER_GEN
        from app.core.llm import get_llm
        from app.core.rag_chain import RAGChain
        from app.core.vectorstore import get_vectorstore
        from app.ingestion.fetcher import fetch_all_data
        from app.ingestion.indexer import index_documents
        from app.ingestion.pokeapi_client import PokeAPIClient
        from app.ingestion.transformers import build_all_documents_for_generation, build_availability_documents

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
                    _ingestion_status = "completed"
                    _ingestion_result = {
                        "status": "skipped",
                        "message": f"ChromaDB already has {count} documents. Use force=true to re-index.",
                        "documents_indexed": 0,
                    }
                    logger.info("Ingestion skipped: already %d documents", count)
                    return

        # Step 1: Fetch all data from PokeAPI
        logger.info("Ingestion: fetching data from PokeAPI...")
        async with PokeAPIClient(cache_dir="data/raw") as client:
            all_data = await fetch_all_data(client, 1025)

        # Step 2: Build documents for each generation
        all_docs = []
        generations = list(range(1, 10))
        for gen in generations:
            if gen not in MAX_POKEMON_PER_GEN:
                continue
            logger.info("Ingestion: building docs for gen %d...", gen)
            docs = build_all_documents_for_generation(all_data, gen)
            all_docs.extend(docs)

        # Cross-generational availability documents (post-processing)
        if all_data.get("encounters"):
            logger.info("Ingestion: building cross-generational availability documents...")
            availability_docs = build_availability_documents(
                all_data["encounters"], all_data["species"],
            )
            all_docs.extend(availability_docs)
            logger.info("Ingestion: %d availability documents added", len(availability_docs))

        logger.info("Ingestion: total %d documents, starting indexing...", len(all_docs))

        # Step 3: Index into ChromaDB
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

        # Step 4: Reload the in-memory vectorstore + RAG chain
        logger.info("Ingestion: reloading vectorstore and RAG chain...")
        new_vs = get_vectorstore(persist_dir, settings.chroma_collection_name, embeddings)
        app_state.vectorstore = new_vs

        llm = get_llm(settings.llm_provider, model=settings.llm_model, temperature=settings.llm_temperature)
        fallback_llm = None
        if settings.llm_fallback_model and settings.llm_fallback_model != settings.llm_model:
            fallback_llm = get_llm(settings.llm_provider, model=settings.llm_fallback_model, temperature=settings.llm_temperature)

        app_state.rag_chain = RAGChain(
            llm=llm, vectorstore=new_vs, k=settings.retriever_k, fallback_llm=fallback_llm,
        )

        elapsed = time.time() - (_ingestion_started_at or 0)
        _ingestion_status = "completed"
        _ingestion_result = {
            "status": "completed",
            "documents_indexed": len(all_docs),
            "elapsed_seconds": round(elapsed, 1),
        }
        logger.info(
            "Ingestion completed: %d documents in %.1fs",
            len(all_docs), elapsed,
        )

    except Exception as exc:
        elapsed = time.time() - (_ingestion_started_at or 0)
        _ingestion_status = "error"
        _ingestion_result = {
            "status": "error",
            "error": str(exc),
            "elapsed_seconds": round(elapsed, 1),
        }
        logger.exception("Ingestion failed after %.1fs: %s", elapsed, exc)


@router.post("/ingest")
async def trigger_ingestion(
    request: Request,
    force: bool = Query(False),
):
    """Start data ingestion in background. Poll /ingest/status for progress."""
    global _ingestion_status, _ingestion_result, _ingestion_started_at

    if _ingestion_status == "running":
        elapsed = time.time() - (_ingestion_started_at or 0)
        return {
            "status": "already_running",
            "message": f"Ingestion already in progress ({round(elapsed)}s elapsed)",
        }

    _ingestion_status = "running"
    _ingestion_result = None
    _ingestion_started_at = time.time()

    asyncio.create_task(_run_ingestion_background(request.app.state, force))

    return {"status": "started", "message": "Ingestion started in background. Poll /ingest/status for progress."}


@router.get("/ingest/status")
async def ingestion_status():
    """Poll ingestion progress."""
    result = {
        "status": _ingestion_status,
        "started_at": _ingestion_started_at,
    }

    if _ingestion_status == "running" and _ingestion_started_at:
        result["elapsed_seconds"] = round(time.time() - _ingestion_started_at, 1)

    if _ingestion_result:
        result.update(_ingestion_result)

    return result


def _get_cache(request: Request) -> ResponseCache:
    cache: ResponseCache | None = getattr(request.app.state, "cache", None)
    if cache is None:
        raise HTTPException(status_code=503, detail="Cache not initialized")
    return cache


@router.get("/cache/stats")
async def cache_stats(request: Request):
    """Return cache statistics (total entries, total hits)."""
    cache = _get_cache(request)
    return await cache.stats()


@router.post("/cache/invalidate")
async def cache_invalidate(request: Request):
    """Clear the entire response cache."""
    cache = _get_cache(request)
    deleted = await cache.invalidate_all()
    return {"status": "ok", "entries_deleted": deleted}


@router.post("/cache/cleanup")
async def cache_cleanup(
    request: Request,
    max_age_days: int = Query(90, description="Remove entries older than N days"),
):
    """Remove stale cache entries that haven't been hit recently."""
    cache = _get_cache(request)
    deleted = await cache.cleanup(max_age_days=max_age_days)
    return {"status": "ok", "stale_entries_removed": deleted}


@router.get("/cache/entries")
async def cache_list_entries(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    reviewed: bool | None = Query(None, description="Filter: true=reviewed, false=not reviewed, omit=all"),
    generation: int | None = Query(None, ge=1, le=9),
    search: str | None = Query(None, description="Search in question text"),
    feedback: str | None = Query(None, description="Filter by feedback: V, F, M, or -"),
    sort_by: str = Query("id", description="Column to sort by: id, generation, created_at, hit_count"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
):
    """List cache entries with pagination, filters and sorting."""
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
    body: UpdateEntryBody = Body(...),
):
    """Update a cache entry's response and/or generation, mark as reviewed."""
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
):
    """Mark a cache entry as reviewed without changing the response."""
    cache = _get_cache(request)
    success = await cache.mark_reviewed(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "ok", "entry_id": entry_id, "reviewed": True}


@router.delete("/cache/entries/{entry_id}")
async def cache_delete_entry(
    request: Request,
    entry_id: int = Path(..., description="Cache entry ID"),
):
    """Delete a single cache entry."""
    cache = _get_cache(request)
    success = await cache.delete_entry(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "ok", "entry_id": entry_id}


@router.post("/cache/rehash")
async def cache_rehash(request: Request):
    """Recompute all hashes after normalization rule changes.

    Run this after deploying new stopwords/synonyms to ensure
    existing entries match queries hashed with the updated rules.
    """
    cache = _get_cache(request)
    result = await cache.rehash_all()
    return {
        "status": "ok",
        "entries_updated": result["updated"],
        "duplicates_found": result["duplicates_found"],
        "duplicates": result["duplicates"],
    }


@router.get("/cache/duplicates")
async def cache_duplicates(
    request: Request,
    generation: int | None = Query(None, description="Filter by generation"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List groups of cache entries that share the same normalized hash.

    Useful for finding and cleaning up duplicate entries, or identifying
    stopwords that incorrectly cause different questions to hash equally.
    """
    cache = _get_cache(request)
    return await cache.list_duplicate_groups(
        generation=generation, page=page, per_page=per_page,
    )


@router.get("/cache/stopwords")
async def list_stopwords(request: Request):
    """List all custom stopwords."""
    cache = _get_cache(request)
    words = await cache.list_stopwords()
    return {"words": words, "total": len(words)}


@router.post("/cache/stopwords")
async def add_stopwords(
    request: Request,
    body: AddStopwordsBody = Body(...),
):
    """Add custom stopwords and rehash all entries."""
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
):
    """Remove a custom stopword and rehash all entries."""
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
    question: str = Query(..., description="Question to analyze"),
    generation: int = Query(9, ge=1, le=9, description="Generation (default 9)"),
):
    """Show how a question would be hashed — no DB writes.

    Use this to verify that two different phrasings produce the same
    normal_hash before testing them in the chatbot.
    """
    return ResponseCache.debug_hash(question, generation)


@router.post("/cache/import")
async def cache_import_csv(
    request: Request,
    file: UploadFile = File(..., description="CSV file with columns: question, generation, response"),
    skip_duplicates: bool = Query(True, description="Skip entries whose normalized hash already exists"),
):
    """Bulk-import cache entries from a CSV file.

    The CSV must have at least these columns: question, generation, response.
    Other columns are ignored. Entries are stored with reviewed=0.
    """
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
async def cache_export_csv(request: Request):
    """Export all cache entries as a CSV file (opens in Excel / Google Sheets)."""
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
async def download_database():
    """Download the full SQLite database file.

    Open it with DB Browser for SQLite (https://sqlitebrowser.org/).
    """
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
