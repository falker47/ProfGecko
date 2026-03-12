"""Shared fixtures for Prof. Gecko backend tests."""

import pytest_asyncio
import aiosqlite
from pathlib import Path


@pytest_asyncio.fixture
async def db_conn():
    """In-memory SQLite database with schema applied."""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    schema = (Path(__file__).parent.parent / "app" / "db" / "schema.sql").read_text()
    await conn.executescript(schema)
    yield conn
    await conn.close()
