"""
Authentication service layer.

Handles user authentication and registration.
"""
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, get_password_hash, create_access_token
from app.domain.user.entity import User
from app.domain.auth.schemas import LoginRequest, RegisterRequest, Token
from app.domain.shared.entity import GlobalRole


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.

        Returns the user if credentials are valid, None otherwise.
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    async def login(self, data: LoginRequest) -> Optional[Token]:
        """
        Login a user and return JWT token.

        Returns Token if successful, None if authentication fails.
        """
        user = await self.authenticate(data.email, data.password)

        if not user:
            return None

        if not user.is_active:
            return None

        access_token = create_access_token(subject=str(user.id))

        return Token(access_token=access_token)

    async def register(self, data: RegisterRequest) -> Optional[User]:
        """
        Register a new user.

        Returns the created user, or None if email already exists.
        """
        # Check if email already exists
        result = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        if result.scalar_one_or_none():
            return None

        user = User(
            id=uuid4(),
            email=data.email,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
            global_role=GlobalRole.USER,
            is_active=True,
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        from uuid import UUID
        try:
            uid = UUID(user_id)
        except ValueError:
            return None

        result = await self.db.execute(
            select(User).where(User.id == uid)
        )
        return result.scalar_one_or_none()