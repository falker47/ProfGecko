"""Tests for JWT creation and verification."""

import time

import jwt as pyjwt
import pytest

from app.auth.jwt import create_access_token, decode_access_token

SECRET = "test-secret-key-that-is-long-enough-for-HS256"


def test_create_and_decode():
    """Round-trip: create → decode returns same user_id."""
    token = create_access_token("user-123", SECRET)
    assert decode_access_token(token, SECRET) == "user-123"


def test_expired_token():
    """Expired tokens raise ExpiredSignatureError."""
    token = create_access_token("user-123", SECRET, expires_hours=0)
    # Token created with 0 hours expiry is already expired
    time.sleep(0.1)
    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_access_token(token, SECRET)


def test_wrong_secret():
    """Token signed with different secret fails verification."""
    token = create_access_token("user-123", SECRET)
    with pytest.raises(pyjwt.InvalidSignatureError):
        decode_access_token(token, "wrong-secret-also-long-enough-for-HS256")


def test_malformed_token():
    """Garbage string raises InvalidTokenError."""
    with pytest.raises(pyjwt.InvalidTokenError):
        decode_access_token("not.a.valid.token", SECRET)
