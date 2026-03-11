from pydantic import BaseModel, Field


class MessageSchema(BaseModel):
    role: str
    content: str = Field(..., max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    chat_history: list[MessageSchema] = Field(default=[], max_length=20)


class ChatResponse(BaseModel):
    answer: str
    generation_used: int


class HealthResponse(BaseModel):
    status: str
    documents_count: int


# --- Auth & Credits ---


class GoogleLoginRequest(BaseModel):
    id_token: str


class UserInfo(BaseModel):
    id: str
    name: str
    email: str
    picture_url: str


class CreditBalance(BaseModel):
    daily_free_remaining: int
    daily_free_total: int
    paid_credits: int
    total_available: int


class AuthResponse(BaseModel):
    access_token: str
    user: UserInfo
    credits: CreditBalance
