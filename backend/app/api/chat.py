import json
from enum import Enum

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.auth.dependencies import get_current_user_optional
from app.core.cache import ResponseCache
from app.core.rag_chain import RAGChain
from app.credits.dependencies import check_and_deduct_credit
from app.models.schemas import ChatRequest, ChatResponse

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

    Cache-hit responses are free (no credit deduction).
    On cache hit, the credit that was pre-deducted is refunded.
    """
    rag_chain: RAGChain = request.app.state.rag_chain
    cache: ResponseCache | None = getattr(request.app.state, "cache", None)
    history = [{"role": m.role, "content": m.content} for m in body.chat_history]
    generation = RAGChain._detect_generation_with_history(body.message, history)

    async def event_generator():
        try:
            async for chunk in rag_chain.astream_cached(
                question=body.message,
                chat_history=history,
                cache=cache,
            ):
                yield {
                    "event": "token",
                    "data": json.dumps({"token": chunk}),
                }
        except Exception as exc:
            import logging
            logging.getLogger(__name__).exception("LLM streaming error")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(exc)}),
            }
            return

        # If cache hit, refund the credit that was pre-deducted
        was_cache_hit = getattr(rag_chain, "_last_cache_hit", False)
        entry_id = getattr(rag_chain, "_last_entry_id", None)
        final_credits = credit_info
        if was_cache_hit and credit_info and user and request.app.state.db:
            from app.config import get_settings
            settings = get_settings()
            db = request.app.state.db
            await db.refund_last_deduction(user["id"])
            final_credits = await db.get_credit_balance(
                user["id"], settings.daily_free_credits
            )

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
