"""
Email verification service.

Handles email verification token generation, validation, and rate limiting.
"""
import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email import EmailMessage, get_email_backend
from app.core.templates import render_email_verification
from app.domain.user.entity import User

logger = logging.getLogger(__name__)

# Token expiration: 7 days
TOKEN_EXPIRATION_DAYS = 7

# Rate limiting: 60 seconds between resend requests
RESEND_COOLDOWN_SECONDS = 60


class EmailVerificationService:
    """
    Service for email verification operations.

    Handles:
    - Generating and sending verification emails
    - Verifying tokens
    - Rate limiting resend requests
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._email_backend = None

    @property
    def email_backend(self):
        """Lazy-load email backend."""
        if self._email_backend is None:
            self._email_backend = get_email_backend()
        return self._email_backend

    def _generate_token(self) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(48)[:64]

    async def generate_and_send_verification(
        self,
        user: User,
        locale: str = "en",
        base_url: Optional[str] = None,
    ) -> bool:
        """
        Generate a verification token and send verification email.

        Args:
            user: The user to send verification to
            locale: The user's locale for email localization
            base_url: Base URL for the verification link

        Returns:
            True if email was sent successfully, False otherwise
        """
        # Generate token
        token = self._generate_token()
        now = datetime.now(timezone.utc)

        # Update user with token
        user.email_verification_token = token
        user.email_verification_sent_at = now
        await self.db.flush()

        # Build verification URL
        if base_url is None:
            base_url = "http://localhost:3000"  # Default for development
        verification_url = f"{base_url}/{locale}/auth/verify-email?token={token}"

        # Render email template
        subject, html_body = render_email_verification(
            locale=locale,
            verification_url=verification_url,
            user_name=user.full_name,
        )

        # Send email
        if not settings.EMAIL_ENABLED:
            logger.info(
                f"Email disabled, would send verification to {user.email}. "
                f"Token: {token}"
            )
            return True

        message = EmailMessage(
            to_email=user.email,
            to_name=user.full_name,
            subject=subject,
            body_html=html_body,
        )

        success = await self.email_backend.send(message)

        if success:
            logger.info(f"Verification email sent to {user.email}")
        else:
            logger.error(f"Failed to send verification email to {user.email}")

        return success

    async def verify_token(self, token: str) -> Optional[User]:
        """
        Verify an email verification token.

        Args:
            token: The verification token

        Returns:
            The verified user if token is valid, None otherwise
        """
        if not token:
            return None

        # Find user by token
        result = await self.db.execute(
            select(User).where(User.email_verification_token == token)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Invalid verification token attempted")
            return None

        # Check token expiration
        if user.email_verification_sent_at:
            expiration = user.email_verification_sent_at + timedelta(
                days=TOKEN_EXPIRATION_DAYS
            )
            if datetime.now(timezone.utc) > expiration:
                logger.warning(f"Expired verification token for user {user.id}")
                return None

        # Mark email as verified
        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_sent_at = None
        await self.db.flush()

        logger.info(f"Email verified for user {user.id}")
        return user

    def can_resend(self, user: User) -> Tuple[bool, int]:
        """
        Check if a verification email can be resent.

        Args:
            user: The user to check

        Returns:
            Tuple of (can_resend, seconds_remaining)
            - can_resend: True if enough time has passed since last send
            - seconds_remaining: Seconds until resend is allowed (0 if can_resend)
        """
        if user.email_verified:
            return False, 0

        if not user.email_verification_sent_at:
            return True, 0

        elapsed = datetime.now(timezone.utc) - user.email_verification_sent_at
        elapsed_seconds = int(elapsed.total_seconds())

        if elapsed_seconds >= RESEND_COOLDOWN_SECONDS:
            return True, 0

        return False, RESEND_COOLDOWN_SECONDS - elapsed_seconds

    async def get_user_by_token(self, token: str) -> Optional[User]:
        """
        Get user by verification token without verifying.

        Useful for checking if a token exists before attempting verification.

        Args:
            token: The verification token

        Returns:
            The user if token exists, None otherwise
        """
        if not token:
            return None

        result = await self.db.execute(
            select(User).where(User.email_verification_token == token)
        )
        return result.scalar_one_or_none()
