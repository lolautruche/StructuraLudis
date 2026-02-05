"""
Authentication service layer.

Handles user authentication and registration.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.domain.user.entity import User
from app.domain.auth.schemas import LoginRequest, RegisterRequest, Token
from app.domain.shared.entity import GlobalRole


class PrivacyPolicyNotAcceptedError(Exception):
    """Raised when user tries to register without accepting privacy policy."""
    pass


class AccountDeactivatedError(Exception):
    """Raised when user tries to login but account is deactivated."""
    pass


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
        Raises AccountDeactivatedError if account is deactivated.
        If remember_me is True, token expires in 30 days instead of 24 hours.
        """
        user = await self.authenticate(data.email, data.password)

        if not user:
            return None

        if not user.is_active:
            raise AccountDeactivatedError()

        # Update last_login timestamp
        user.last_login = datetime.now(timezone.utc)
        await self.db.flush()

        # Use longer expiration for "remember me"
        expires_delta = None
        if data.remember_me:
            expires_delta = timedelta(days=settings.REMEMBER_ME_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=expires_delta,
        )

        return Token(access_token=access_token)

    async def register(self, data: RegisterRequest, locale: str = "en") -> Optional[User]:
        """
        Register a new user.

        Returns the created user, or None if email already exists.
        Raises PrivacyPolicyNotAcceptedError if privacy policy not accepted.

        Args:
            data: Registration data
            locale: User's preferred locale (from Accept-Language header)
        """
        # GDPR: Privacy policy must be accepted
        if not data.accept_privacy_policy:
            raise PrivacyPolicyNotAcceptedError()

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
            privacy_accepted_at=datetime.now(timezone.utc),
            locale=locale,
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