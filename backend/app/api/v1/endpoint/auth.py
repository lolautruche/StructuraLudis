"""
Authentication API endpoints.

Login, registration, token management, and email verification.
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.domain.auth.schemas import LoginRequest, RegisterRequest, Token
from app.domain.user.entity import User
from app.domain.user.schemas import UserRead
from app.services.auth import AuthService, PrivacyPolicyNotAcceptedError
from app.services.email_verification import EmailVerificationService
from app.api.deps import get_current_active_user


def _parse_locale_from_header(accept_language: Optional[str]) -> str:
    """Extract locale from Accept-Language header, defaulting to 'en'."""
    if not accept_language:
        return "en"
    # Parse first language from header (e.g., "fr-FR,fr;q=0.9,en;q=0.8" -> "fr")
    first_lang = accept_language.split(",")[0].split(";")[0].strip()
    # Extract base language (e.g., "fr-FR" -> "fr")
    base_lang = first_lang.split("-")[0].lower()
    # Only support known locales
    if base_lang in ("fr", "en"):
        return base_lang
    return "en"

router = APIRouter()


class EmailVerificationResponse(BaseModel):
    """Response for email verification."""
    success: bool
    message: str


class ResendVerificationResponse(BaseModel):
    """Response for resend verification."""
    success: bool
    message: str
    seconds_remaining: int = 0


@router.post("/login", response_model=Token)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password.

    Returns JWT access token on success.
    Note: Login is allowed even if email is not verified.
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
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
):
    """
    Register a new user account.

    Requires acceptance of the privacy policy.
    Returns the created user on success.
    A verification email is sent to the user's email address.
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

    # Send verification email
    verification_service = EmailVerificationService(db)

    # Use configured frontend URL for verification links
    frontend_base_url = settings.FRONTEND_URL

    # Get locale from Accept-Language header (user hasn't set preference yet at registration)
    locale = _parse_locale_from_header(accept_language)

    await verification_service.generate_and_send_verification(
        user=user,
        locale=locale,
        base_url=frontend_base_url,
    )

    await db.commit()
    await db.refresh(user)
    return user


@router.get("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    token: str = Query(..., description="Email verification token"),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify a user's email address using the token from the verification email.

    Returns success status and message.
    """
    verification_service = EmailVerificationService(db)
    user = await verification_service.verify_token(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    await db.commit()
    return EmailVerificationResponse(
        success=True,
        message="Email verified successfully. You can now access all features.",
    )


@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
):
    """
    Resend the verification email to the current user.

    Rate limited to 1 request per 60 seconds.
    Requires authentication.
    """
    if current_user.email_verified:
        return ResendVerificationResponse(
            success=False,
            message="Email is already verified.",
            seconds_remaining=0,
        )

    verification_service = EmailVerificationService(db)
    can_resend, seconds_remaining = verification_service.can_resend(current_user)

    if not can_resend:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {seconds_remaining} seconds before requesting another verification email.",
            headers={"Retry-After": str(seconds_remaining)},
        )

    # Use configured frontend URL for verification links
    frontend_base_url = settings.FRONTEND_URL

    # Get locale from Accept-Language header (reflects current UI language)
    locale = _parse_locale_from_header(accept_language)

    success = await verification_service.generate_and_send_verification(
        user=current_user,
        locale=locale,
        base_url=frontend_base_url,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later.",
        )

    await db.commit()
    return ResendVerificationResponse(
        success=True,
        message="Verification email sent. Please check your inbox.",
        seconds_remaining=0,
    )
