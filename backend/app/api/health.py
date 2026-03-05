from fastapi import APIRouter, Request

from app.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    vectorstore = request.app.state.vectorstore
    count = vectorstore._collection.count()
    return HealthResponse(status="ok", documents_count=count)
