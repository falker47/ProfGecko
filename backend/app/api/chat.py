import json

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from app.core.rag_chain import RAGChain
from app.credits.dependencies import check_and_deduct_credit
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()


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
):
    """SSE streaming: sends tokens as they are generated."""
    rag_chain: RAGChain = request.app.state.rag_chain
    history = [{"role": m.role, "content": m.content} for m in body.chat_history]
    generation = RAGChain._detect_generation_with_history(body.message, history)

    async def event_generator():
        async for chunk in rag_chain.astream(
            question=body.message,
            chat_history=history,
        ):
            yield {
                "event": "token",
                "data": json.dumps({"token": chunk}),
            }
        yield {
            "event": "done",
            "data": json.dumps({
                "generation_used": generation,
                "credits": credit_info,
            }),
        }

    return EventSourceResponse(event_generator())
