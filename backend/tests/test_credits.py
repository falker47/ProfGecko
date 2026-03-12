"""Tests for the credit system (Database class methods).

Uses an in-memory SQLite database (conftest.py fixture).
"""

import pytest
import pytest_asyncio

from app.db.database import Database


@pytest_asyncio.fixture
async def db(db_conn):
    """Create a Database instance wrapping the in-memory connection."""
    database = Database(":memory:")
    database._conn = db_conn
    return database


@pytest_asyncio.fixture
async def user(db):
    """Create a test user and return its dict."""
    return await db.upsert_user(
        google_id="g-123",
        email="ash@pokemon.com",
        name="Ash Ketchum",
        picture_url="https://example.com/ash.png",
    )


DAILY_FREE = 10  # matches default config


@pytest.mark.asyncio
class TestCreditBalance:
    async def test_initial_balance(self, db, user):
        """New user has full daily free credits and 0 paid."""
        balance = await db.get_credit_balance(user["id"], DAILY_FREE)
        assert balance["daily_free_remaining"] == DAILY_FREE
        assert balance["paid_credits"] == 0
        assert balance["total_available"] == DAILY_FREE

    async def test_free_deduction(self, db, user):
        """Free deduction decreases daily_free_remaining."""
        await db.record_deduction(user["id"], "daily_free_deduction")
        balance = await db.get_credit_balance(user["id"], DAILY_FREE)
        assert balance["daily_free_remaining"] == DAILY_FREE - 1
        assert balance["paid_credits"] == 0

    async def test_paid_deduction(self, db, user):
        """Paid deduction decreases paid_credits."""
        # Give user some paid credits first
        await db.add_purchased_credits(user["id"], 5, "stripe_sess_1")
        await db.record_deduction(user["id"], "paid_deduction")
        balance = await db.get_credit_balance(user["id"], DAILY_FREE)
        assert balance["paid_credits"] == 4

    async def test_refund_free_deduction(self, db, user):
        """Refunding a free deduction restores daily_free_remaining."""
        await db.record_deduction(user["id"], "daily_free_deduction")
        await db.refund_last_deduction(user["id"])
        balance = await db.get_credit_balance(user["id"], DAILY_FREE)
        assert balance["daily_free_remaining"] == DAILY_FREE

    async def test_refund_paid_deduction(self, db, user):
        """Refunding a paid deduction restores paid_credits."""
        await db.add_purchased_credits(user["id"], 5, "stripe_sess_2")
        await db.record_deduction(user["id"], "paid_deduction")
        await db.refund_last_deduction(user["id"])
        balance = await db.get_credit_balance(user["id"], DAILY_FREE)
        assert balance["paid_credits"] == 5


@pytest.mark.asyncio
class TestPurchaseIdempotency:
    async def test_duplicate_stripe_session(self, db, user):
        """Same stripe_session_id only processes once."""
        await db.add_purchased_credits(user["id"], 10, "stripe_dup")
        await db.add_purchased_credits(user["id"], 10, "stripe_dup")
        balance = await db.get_credit_balance(user["id"], DAILY_FREE)
        assert balance["paid_credits"] == 10  # not 20


@pytest.mark.asyncio
class TestUpsertUser:
    async def test_create_user(self, db):
        """First upsert creates a new user."""
        user = await db.upsert_user("g-new", "new@test.com", "New User", "")
        assert user["email"] == "new@test.com"
        assert user["google_id"] == "g-new"

    async def test_update_user(self, db):
        """Second upsert with same google_id updates the record."""
        await db.upsert_user("g-up", "old@test.com", "Old Name", "")
        user = await db.upsert_user("g-up", "new@test.com", "New Name", "pic.png")
        assert user["email"] == "new@test.com"
        assert user["name"] == "New Name"
