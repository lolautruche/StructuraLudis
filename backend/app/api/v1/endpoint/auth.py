"""
Authentication API endpoints.

Login, registration, token management, email verification, and password reset.
"""
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.email import EmailMessage, get_email_backend
from app.core.security import get_password_hash
from app.core.templates import render_password_reset, render_password_changed
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


# =============================================================================
# Password Reset
# =============================================================================

# Token expiration: 1 hour
PASSWORD_RESET_TOKEN_EXPIRATION_HOURS = 1


class ForgotPasswordRequest(BaseModel):
    """Schema for requesting password reset."""
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Response for password reset request."""
    success: bool
    message: str


class ResetPasswordRequest(BaseModel):
    """Schema for resetting password with token."""
    token: str
    new_password: str = Field(..., min_length=8)


class ResetPasswordResponse(BaseModel):
    """Response for password reset."""
    success: bool
    message: str


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
):
    """
    Request a password reset.

    Sends a reset email if the email exists.
    Always returns success to prevent email enumeration.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == data.email.lower())
    )
    user = result.scalar_one_or_none()

    if user and user.is_active:
        # Generate reset token
        token = secrets.token_urlsafe(48)[:64]
        now = datetime.now(timezone.utc)

        # Store token
        user.password_reset_token = token
        user.password_reset_sent_at = now
        await db.flush()

        # Build reset URL
        locale = _parse_locale_from_header(accept_language)
        frontend_base_url = settings.FRONTEND_URL
        reset_url = f"{frontend_base_url}/{locale}/auth/reset-password?token={token}"

        # Render and send email
        subject, html_body = render_password_reset(
            locale=locale,
            reset_url=reset_url,
            user_name=user.full_name,
        )

        if settings.EMAIL_ENABLED:
            email_backend = get_email_backend()
            message = EmailMessage(
                to_email=user.email,
                to_name=user.full_name,
                subject=subject,
                body_html=html_body,
            )
            await email_backend.send(message)

        await db.commit()

    # Always return success to prevent email enumeration
    return ForgotPasswordResponse(
        success=True,
        message="If an account with this email exists, a password reset link has been sent.",
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
):
    """
    Reset password using the token from email.

    Validates the token and sets the new password.
    """
    if not data.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required",
        )

    # Find user by reset token
    result = await db.execute(
        select(User).where(User.password_reset_token == data.token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Check token expiration
    if user.password_reset_sent_at:
        expiration = user.password_reset_sent_at + timedelta(
            hours=PASSWORD_RESET_TOKEN_EXPIRATION_HOURS
        )
        if datetime.now(timezone.utc) > expiration:
            # Clear expired token
            user.password_reset_token = None
            user.password_reset_sent_at = None
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired. Please request a new one.",
            )

    # Update password
    user.hashed_password = get_password_hash(data.new_password)
    user.password_reset_token = None
    user.password_reset_sent_at = None

    # Send notification email about password change
    if settings.EMAIL_ENABLED:
        locale = _parse_locale_from_header(accept_language)
        changed_at = datetime.now(timezone.utc)
        subject, html_body = render_password_changed(
            locale=locale,
            changed_at=changed_at,
            user_name=user.full_name,
        )

        email_backend = get_email_backend()
        message = EmailMessage(
            to_email=user.email,
            to_name=user.full_name,
            subject=subject,
            body_html=html_body,
        )
        await email_backend.send(message)

    await db.commit()

    return ResetPasswordResponse(
        success=True,
        message="Password reset successfully. You can now log in with your new password.",
    )
