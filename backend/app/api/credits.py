"""Credit balance endpoints."""

from fastapi import APIRouter, Depends, Request

from app.auth.dependencies import get_current_user_required
from app.config import get_settings
from app.models.schemas import CreditBalance

router = APIRouter(prefix="/credits", tags=["credits"])


@router.get("", response_model=CreditBalance)
async def get_credits(
    request: Request,
    user: dict = Depends(get_current_user_required),
):
    """Return the current credit balance for the authenticated user."""
    settings = get_settings()
    db = request.app.state.db
    balance = await db.get_credit_balance(user["id"], settings.daily_free_credits)
    return CreditBalance(**balance)
