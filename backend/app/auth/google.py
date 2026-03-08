"""Google ID token verification."""

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


def verify_google_token(token: str, client_id: str) -> dict:
    """Verify a Google ID token and return user info.

    Returns:
        ``{"google_id": ..., "email": ..., "name": ..., "picture": ...}``

    Raises:
        ``ValueError`` if the token is invalid or expired.
    """
    idinfo = id_token.verify_oauth2_token(
        token,
        google_requests.Request(),
        client_id,
    )
    return {
        "google_id": idinfo["sub"],
        "email": idinfo["email"],
        "name": idinfo.get("name", ""),
        "picture": idinfo.get("picture", ""),
    }
