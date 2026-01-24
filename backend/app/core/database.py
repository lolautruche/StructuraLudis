"""
Database configuration and session management.

Similar to Doctrine's EntityManager configuration in Symfony.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Import all models to ensure relationships are resolved
# Similar to Doctrine's entity mapping in Symfony
from app.domain.models import Base  # noqa: F401 - imports all entities

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    Similar to Doctrine's EntityManager injection in Symfony controllers.

    Usage:
        @router.get("/")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Re-export Base for convenience
__all__ = ["Base", "engine", "AsyncSessionLocal", "get_db"]