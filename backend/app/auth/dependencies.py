"""FastAPI dependencies for authentication."""

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


async def verify_admin_secret(
    request: Request,
    x_admin_secret: str = Header(..., alias="X-Admin-Secret"),
) -> None:
    """Verify the admin secret passed via X-Admin-Secret header."""
    if x_admin_secret != request.app.state.jwt_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict | None:
    """Return user dict if a valid Bearer token is present, else ``None``."""
    if credentials is None:
        return None
    try:
        user_id = decode_access_token(
            credentials.credentials,
            request.app.state.jwt_secret,
        )
        user = await request.app.state.db.get_user_by_id(user_id)
        return user
    except Exception:
        return None


async def get_current_user_required(
    user: dict | None = Depends(get_current_user_optional),
) -> dict:
    """Require authentication. Raises 401 if not authenticated."""
    if user is None:
        raise HTTPException(status_code=401, detail="Autenticazione richiesta")
    return user
