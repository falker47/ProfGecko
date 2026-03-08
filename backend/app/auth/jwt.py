"""JWT creation and verification."""

from datetime import datetime, timedelta, timezone

import jwt


def create_access_token(
    user_id: str,
    secret: str,
    expires_hours: int = 168,
) -> str:
    """Create a signed JWT with the user ID as subject."""
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str, secret: str) -> str:
    """Decode and verify a JWT. Returns the user ID.

    Raises:
        ``jwt.InvalidTokenError`` on invalid or expired tokens.
    """
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    return payload["sub"]
