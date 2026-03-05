from pydantic import BaseModel


class MessageSchema(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    chat_history: list[MessageSchema] = []


class ChatResponse(BaseModel):
    answer: str
    generation_used: int


class HealthResponse(BaseModel):
    status: str
    documents_count: int
