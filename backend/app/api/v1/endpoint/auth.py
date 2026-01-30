"""
Authentication API endpoints.

Login, registration, and token management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.auth.schemas import LoginRequest, RegisterRequest, Token
from app.domain.user.schemas import UserRead
from app.services.auth import AuthService, PrivacyPolicyNotAcceptedError

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password.

    Returns JWT access token on success.
    """
    service = AuthService(db)
    token = await service.login(data)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.

    Requires acceptance of the privacy policy.
    Returns the created user on success.
    """
    service = AuthService(db)

    try:
        user = await service.register(data)
    except PrivacyPolicyNotAcceptedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the privacy policy to register",
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    return user