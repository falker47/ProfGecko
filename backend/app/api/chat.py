import json

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.core.generation_mapper import LATEST_GENERATION, detect_generation
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    """Synchronous chat: returns full response as JSON."""
    rag_chain = request.app.state.rag_chain
    history = [{"role": m.role, "content": m.content} for m in body.chat_history]

    answer = await rag_chain.ainvoke(
        question=body.message,
        chat_history=history,
    )

    generation = detect_generation(body.message) or LATEST_GENERATION
    return ChatResponse(answer=answer, generation_used=generation)


@router.post("/chat/stream")
async def chat_stream(request: Request, body: ChatRequest):
    """SSE streaming: sends tokens as they are generated."""
    rag_chain = request.app.state.rag_chain
    history = [{"role": m.role, "content": m.content} for m in body.chat_history]
    generation = detect_generation(body.message) or LATEST_GENERATION

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
            "data": json.dumps({"generation_used": generation}),
        }

    return EventSourceResponse(event_generator())
