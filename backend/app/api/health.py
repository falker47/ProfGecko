import logging
import traceback

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.models.schemas import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health(request: Request):
    try:
        vectorstore = getattr(request.app.state, "vectorstore", None)
        if vectorstore is None:
            return JSONResponse(
                status_code=503,
                content={"status": "error", "detail": "vectorstore not initialized"},
            )
        count = vectorstore._collection.count()
        return {"status": "ok", "documents_count": count}
    except Exception as exc:
        logger.exception("Health check failed")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
