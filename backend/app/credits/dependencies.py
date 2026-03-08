"""FastAPI dependency for credit checking and deduction."""

from fastapi import Depends, HTTPException, Request

from app.auth.dependencies import get_current_user_optional
from app.config import get_settings


async def check_and_deduct_credit(
    request: Request,
    user: dict | None = Depends(get_current_user_optional),
) -> dict | None:
    """Check credit balance and deduct 1 credit before chat.

    - Anonymous users (``user is None``): no enforcement, returns ``None``.
    - Authenticated users: deducts 1 credit (daily free first, then paid).
    - Raises HTTP 402 if no credits remain.
    """
    if user is None:
        return None

    settings = get_settings()
    db = request.app.state.db
    balance = await db.get_credit_balance(user["id"], settings.daily_free_credits)

    if balance["total_available"] <= 0:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "no_credits",
                "message": "Hai esaurito i crediti! "
                "I crediti gratuiti si resettano a mezzanotte.",
            },
        )

    # Deduct: daily free credits first, then paid
    if balance["daily_free_remaining"] > 0:
        await db.record_deduction(user["id"], "daily_free_deduction")
    else:
        await db.record_deduction(user["id"], "paid_deduction")

    # Return updated balance
    return await db.get_credit_balance(user["id"], settings.daily_free_credits)
