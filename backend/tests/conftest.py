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
from app.domain.shared.entity import GlobalRole, UserGroupType, GroupRole
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
        for table in ["bookings", "game_sessions", "physical_tables", "zones",
                      "time_slots", "games", "game_categories",
                      "user_group_memberships", "group_permissions", "user_groups",
                      "exhibitions", "media", "audit_logs", "users", "organizations"]:
            try:
                await conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            except Exception:
                pass  # Table might not exist yet


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client (no auth)."""

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


@pytest.fixture
async def test_user(db_session: AsyncSession) -> dict:
    """Create a test user with USER role."""
    from app.domain.user.entity import User

    user = User(
        id=uuid4(),
        email="testuser@example.com",
        hashed_password="hashed_test_password",
        full_name="Test User",
        global_role=GlobalRole.USER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "global_role": str(user.global_role),
    }


@pytest.fixture
async def test_organizer(db_session: AsyncSession, test_organization: dict) -> dict:
    """Create a test user with ORGANIZER role, linked to test organization."""
    from app.domain.user.entity import User, UserGroupMembership
    from app.domain.organization.entity import UserGroup

    # Create user
    user = User(
        id=uuid4(),
        email="organizer@example.com",
        hashed_password="hashed_test_password",
        full_name="Test Organizer",
        global_role=GlobalRole.ORGANIZER,
        is_active=True,
    )
    db_session.add(user)

    # Create user group for the organization
    group = UserGroup(
        id=uuid4(),
        organization_id=test_organization["id"],
        name="Staff",
        type=UserGroupType.STAFF,
        is_public=False,
    )
    db_session.add(group)

    # Add user to group
    membership = UserGroupMembership(
        id=uuid4(),
        user_id=user.id,
        user_group_id=group.id,
        group_role=GroupRole.OWNER,
    )
    db_session.add(membership)

    await db_session.commit()
    await db_session.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "global_role": str(user.global_role),
        "organization_id": test_organization["id"],
        "group_id": str(group.id),
    }


@pytest.fixture
async def test_super_admin(db_session: AsyncSession) -> dict:
    """Create a test user with SUPER_ADMIN role."""
    from app.domain.user.entity import User

    user = User(
        id=uuid4(),
        email="superadmin@example.com",
        hashed_password="hashed_test_password",
        full_name="Super Admin",
        global_role=GlobalRole.SUPER_ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "global_role": str(user.global_role),
    }


@pytest.fixture
async def auth_client(
    db_session: AsyncSession, test_organizer: dict
) -> AsyncGenerator[AsyncClient, None]:
    """Create an authenticated test HTTP client (as organizer)."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-User-ID": test_organizer["id"]},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def admin_client(
    db_session: AsyncSession, test_super_admin: dict
) -> AsyncGenerator[AsyncClient, None]:
    """Create an authenticated test HTTP client (as super admin)."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-User-ID": test_super_admin["id"]},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def second_organizer(db_session: AsyncSession, test_organization: dict) -> dict:
    """Create a second organizer for multi-GM tests."""
    from app.domain.user.entity import User, UserGroupMembership
    from app.domain.organization.entity import UserGroup

    # Create user
    user = User(
        id=uuid4(),
        email="organizer2@example.com",
        hashed_password="hashed_test_password",
        full_name="Second Organizer",
        global_role=GlobalRole.ORGANIZER,
        is_active=True,
    )
    db_session.add(user)

    # Create user group for the organization
    group = UserGroup(
        id=uuid4(),
        organization_id=test_organization["id"],
        name="Staff 2",
        type=UserGroupType.STAFF,
        is_public=False,
    )
    db_session.add(group)

    # Add user to group
    membership = UserGroupMembership(
        id=uuid4(),
        user_id=user.id,
        user_group_id=group.id,
        group_role=GroupRole.OWNER,
    )
    db_session.add(membership)

    await db_session.commit()
    await db_session.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "global_role": str(user.global_role),
        "organization_id": test_organization["id"],
        "group_id": str(group.id),
    }


@pytest.fixture
async def second_auth_client(
    db_session: AsyncSession, second_organizer: dict
) -> AsyncGenerator[AsyncClient, None]:
    """Create an authenticated test HTTP client (as second organizer)."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-User-ID": second_organizer["id"]},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
