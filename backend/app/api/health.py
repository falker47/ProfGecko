import logging

from fastapi import APIRouter, Request

from app.models.schemas import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    try:
        vectorstore = request.app.state.vectorstore
        count = vectorstore._collection.count()
        return HealthResponse(status="ok", documents_count=count)
    except Exception as exc:
        logger.exception("Health check failed")
        raise
