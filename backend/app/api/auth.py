"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.rate_limit import limiter
from app.auth.dependencies import get_current_user_required
from app.auth.google import verify_google_token
from app.auth.jwt import create_access_token
from app.config import get_settings
from app.models.schemas import AuthResponse, CreditBalance, GoogleLoginRequest, UserInfo

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login_with_google(request: Request, body: GoogleLoginRequest):
    """Verify Google ID token, create/update user, return JWT."""
    settings = get_settings()

    if not settings.google_client_id:
        raise HTTPException(500, "Google OAuth non configurato sul server")

    try:
        google_info = verify_google_token(body.id_token, settings.google_client_id)
    except ValueError:
        raise HTTPException(401, "Token Google non valido o scaduto")

    db = request.app.state.db
    user = await db.upsert_user(
        google_id=google_info["google_id"],
        email=google_info["email"],
        name=google_info["name"],
        picture_url=google_info["picture"],
    )

    token = create_access_token(
        user_id=user["id"],
        secret=request.app.state.jwt_secret,
        expires_hours=settings.jwt_expiry_hours,
    )

    balance = await db.get_credit_balance(user["id"], settings.daily_free_credits)

    return AuthResponse(
        access_token=token,
        user=UserInfo(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            picture_url=user["picture_url"],
        ),
        credits=CreditBalance(**balance),
    )


@router.get("/me", response_model=AuthResponse)
async def get_me(
    request: Request,
    user: dict = Depends(get_current_user_required),
):
    """Validate JWT and return current user info + credits."""
    settings = get_settings()
    db = request.app.state.db
    balance = await db.get_credit_balance(user["id"], settings.daily_free_credits)

    # Generate a fresh token (extends session on every page reload)
    token = create_access_token(
        user_id=user["id"],
        secret=request.app.state.jwt_secret,
        expires_hours=settings.jwt_expiry_hours,
    )

    return AuthResponse(
        access_token=token,
        user=UserInfo(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            picture_url=user["picture_url"],
        ),
        credits=CreditBalance(**balance),
    )
