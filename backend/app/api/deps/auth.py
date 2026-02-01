"""
Authentication dependencies.

Provides current user injection for API endpoints.
Supports JWT Bearer tokens and X-User-ID header (for testing).
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.domain.user.entity import User


# Optional bearer scheme - allows endpoints to work with or without auth header
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user.

    Supports:
    - JWT Bearer token (Authorization: Bearer <token>)
    - X-User-ID header (for testing/development)
    """
    user_id: Optional[str] = None

    # Try JWT token first
    if credentials:
        user_id = decode_access_token(credentials.credentials)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    # Fall back to X-User-ID header (for testing)
    elif x_user_id:
        user_id = x_user_id
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        uid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
        )

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get current authenticated user, or None if not authenticated.

    Same as get_current_user but returns None instead of raising 401.
    Useful for endpoints that work differently for authenticated vs anonymous users.
    """
    user_id: Optional[str] = None

    # Try JWT token first
    if credentials:
        user_id = decode_access_token(credentials.credentials)
        if not user_id:
            return None  # Invalid token = not authenticated
    # Fall back to X-User-ID header (for testing)
    elif x_user_id:
        user_id = x_user_id
    else:
        return None  # No auth provided

    try:
        uid = UUID(user_id)
    except ValueError:
        return None

    result = await db.execute(select(User).where(User.id == uid))
    return result.scalar_one_or_none()


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deactivated",
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Ensure the current user has verified their email.

    Used for actions that require email verification (e.g., booking sessions).
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email to perform this action.",
        )
    return current_user
