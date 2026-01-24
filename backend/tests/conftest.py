"""
Test fixtures and configuration.
"""
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import get_db
from app.domain.models import Base
from app.main import app

# Test database URL (same as dev for now, could be separate)
TEST_DATABASE_URL = settings.DATABASE_URL


@pytest.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    Each test runs in isolation with a clean state.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()

    # Clean up tables after each test
    async with test_engine.begin() as conn:
        # Truncate in correct order (respecting FKs)
        for table in ["table_participants", "game_tables", "time_slots",
                      "games", "game_categories", "user_group_memberships",
                      "group_permissions", "user_groups", "exhibitions",
                      "media", "audit_logs", "users", "organizations"]:
            try:
                await conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            except Exception:
                pass  # Table might not exist yet


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_organization(db_session: AsyncSession) -> dict:
    """Create a test organization."""
    from app.domain.organization import Organization

    org = Organization(
        id=uuid4(),
        name="Test Convention",
        slug="test-convention",
        contact_email="test@example.com",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
    }
