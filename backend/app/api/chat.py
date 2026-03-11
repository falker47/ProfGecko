import json
import logging
from enum import Enum

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.auth.dependencies import get_current_user_optional
from app.config import get_settings
from app.core.cache import ResponseCache
from app.core.rag_chain import RAGChain
from app.credits.dependencies import check_and_deduct_credit
from app.models.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter()


class FeedbackValue(str, Enum):
    V = "V"
    F = "F"


class FeedbackBody(BaseModel):
    entry_id: int
    feedback: FeedbackValue


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: Request,
    body: ChatRequest,
    credit_info: dict | None = Depends(check_and_deduct_credit),
):
    """Synchronous chat: returns full response as JSON."""
    rag_chain: RAGChain = request.app.state.rag_chain
    history = [{"role": m.role, "content": m.content} for m in body.chat_history]

    answer = await rag_chain.ainvoke(
        question=body.message,
        chat_history=history,
    )

    generation = RAGChain._detect_generation_with_history(body.message, history)
    return ChatResponse(answer=answer, generation_used=generation)


@router.post("/chat/stream")
async def chat_stream(
    request: Request,
    body: ChatRequest,
    credit_info: dict | None = Depends(check_and_deduct_credit),
    user: dict | None = Depends(get_current_user_optional),
):
    """SSE streaming: sends tokens as they are generated.

    Credits are pre-deducted, then refunded in two cases:
    - Cache hit: already answered, no LLM cost incurred.
    - Missing info: the LLM couldn't answer from the available context.
    """
    rag_chain: RAGChain = request.app.state.rag_chain
    cache: ResponseCache | None = getattr(request.app.state, "cache", None)
    history = [{"role": m.role, "content": m.content} for m in body.chat_history]
    generation = RAGChain._detect_generation_with_history(body.message, history)

    # Per-request metadata dict — avoids shared state on rag_chain instance
    meta: dict = {}

    async def event_generator():
        try:
            async for chunk in rag_chain.astream_cached(
                question=body.message,
                chat_history=history,
                cache=cache,
                metadata=meta,
            ):
                yield {
                    "event": "token",
                    "data": json.dumps({"token": chunk}),
                }
        except Exception as exc:
            logger.exception("LLM streaming error")
            err_str = str(exc)
            # Extract model name from error for debugging
            model_hint = ""
            if "flash-lite" in err_str or "gemini-2.5-flash-lite" in err_str:
                model_hint = " (fallback: gemini-2.5-flash-lite)"
            elif "gemini-2.5" in err_str:
                model_hint = " (primario: gemini-2.5-flash)"
            if "429" in err_str or "quota" in err_str.lower():
                user_msg = f"Il servizio AI ha raggiunto il limite di richieste{model_hint}. Riprova tra qualche minuto."
            else:
                user_msg = "Errore nella generazione della risposta. Riprova tra poco."
            yield {
                "event": "error",
                "data": json.dumps({"error": user_msg}),
            }
            return

        # Refund the pre-deducted credit when:
        # - cache hit (already answered, no LLM cost)
        # - missing info response (LLM couldn't answer from context)
        was_cache_hit = meta.get("cache_hit", False)
        was_missing = meta.get("was_missing", False)
        entry_id = meta.get("entry_id")
        final_credits = credit_info
        should_refund = was_cache_hit or was_missing
        if should_refund and credit_info and user and request.app.state.db:
            try:
                settings = get_settings()
                db = request.app.state.db
                await db.refund_last_deduction(user["id"])
                final_credits = await db.get_credit_balance(
                    user["id"], settings.daily_free_credits
                )
            except Exception:
                logger.exception("Failed to refund credit for user %s", user["id"])

        yield {
            "event": "done",
            "data": json.dumps({
                "generation_used": generation,
                "credits": final_credits,
                "cached": was_cache_hit,
                "entry_id": entry_id,
            }),
        }

    return EventSourceResponse(event_generator())


@router.post("/chat/feedback")
async def submit_feedback(
    request: Request,
    body: FeedbackBody = Body(...),
):
    """Submit user feedback on a cached response.

    Public endpoint (no admin secret). Only allows V (correct) or F (wrong).

    Usage:
        POST /api/chat/feedback
        Body: {"entry_id": 42, "feedback": "V"}
    """
    cache: ResponseCache | None = getattr(request.app.state, "cache", None)
    if cache is None:
        raise HTTPException(status_code=503, detail="Cache not initialized")

    success = await cache.set_feedback(body.entry_id, body.feedback.value)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "ok", "entry_id": body.entry_id, "feedback": body.feedback.value}
