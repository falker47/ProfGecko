"""Rate limiting configuration for API endpoints.

Uses slowapi (built on top of the `limits` library) with in-memory
storage.  Limits are per-IP by default; authenticated users are
identified by their JWT user ID when available.
"""

import logging

from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


def _key_func(request: Request) -> str:
    """Identify the caller by JWT user ID (if authenticated) or IP."""
    # Try to extract user ID from the Authorization header without
    # raising — rate limiting must never crash the request pipeline.
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            import jwt as pyjwt

            token = auth[7:]
            secret = getattr(request.app.state, "jwt_secret", "")
            payload = pyjwt.decode(token, secret, algorithms=["HS256"])
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=_key_func)


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded,
) -> JSONResponse:
    """Return a friendly 429 response when rate limit is hit."""
    logger.warning(
        "Rate limit exceeded: %s %s from %s",
        request.method,
        request.url.path,
        _key_func(request),
    )
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Troppe richieste. Riprova tra qualche secondo.",
            "retry_after": exc.detail,
        },
    )
