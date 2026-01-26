#!/usr/bin/env python3
"""
Initialize the first Super Admin account.

Usage:
    python scripts/init_super_admin.py

Environment variables:
    SUPER_ADMIN_EMAIL: Email for the super admin (default: admin@structuraludis.local)
    SUPER_ADMIN_PASSWORD: Password for the super admin (required)
"""
import asyncio
import os
import sys
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.domain.user.entity import User
from app.domain.shared.entity import GlobalRole


async def create_super_admin(
    email: str,
    password: str,
    full_name: str = "Super Admin",
) -> None:
    """Create the first super admin account."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        # Check if any super admin exists
        result = await session.execute(
            select(User).where(User.global_role == GlobalRole.SUPER_ADMIN)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Super Admin already exists: {existing.email}")
            print("Skipping creation.")
            return

        # Check if email is already taken
        result = await session.execute(
            select(User).where(User.email == email)
        )
        if result.scalar_one_or_none():
            print(f"Email {email} is already in use.")
            sys.exit(1)

        # Create super admin
        # Note: In production, use proper password hashing (bcrypt, argon2)
        user = User(
            id=uuid4(),
            email=email,
            hashed_password=f"hashed_{password}",  # TODO: Use proper hashing
            full_name=full_name,
            global_role=GlobalRole.SUPER_ADMIN,
            is_active=True,
        )
        session.add(user)
        await session.commit()

        print(f"✓ Super Admin created successfully!")
        print(f"  Email: {email}")
        print(f"  ID: {user.id}")

    await engine.dispose()


def main():
    email = os.environ.get("SUPER_ADMIN_EMAIL", "admin@structuraludis.dev")
    password = os.environ.get("SUPER_ADMIN_PASSWORD")

    if not password:
        print("Error: SUPER_ADMIN_PASSWORD environment variable is required")
        print("Usage: SUPER_ADMIN_PASSWORD=mysecret python scripts/init_super_admin.py")
        sys.exit(1)

    if len(password) < 8:
        print("Error: Password must be at least 8 characters")
        sys.exit(1)

    asyncio.run(create_super_admin(email, password))


if __name__ == "__main__":
    main()
