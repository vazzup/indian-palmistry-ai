"""
Pytest configuration and shared fixtures.

This module provides common test fixtures and configuration
for the Indian palmistry AI test suite.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_engine, AsyncSessionLocal, create_tables, drop_tables
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client for FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Set up test database."""
    if not settings.is_sqlite:
        pytest.skip("Tests require SQLite database")
    
    # Create tables
    await create_tables()
    yield
    # Cleanup after tests
    await drop_tables()


@pytest.fixture
async def db_session():
    """Create database session for tests."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()