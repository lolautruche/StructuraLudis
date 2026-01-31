"""
Tests for Email Verification Service.
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user.entity import User
from app.domain.shared.entity import GlobalRole
from app.services.email_verification import (
    EmailVerificationService,
    TOKEN_EXPIRATION_DAYS,
    RESEND_COOLDOWN_SECONDS,
)


class TestEmailVerificationService:
    """Tests for EmailVerificationService."""

    @pytest.fixture
    async def unverified_user(self, db_session: AsyncSession) -> User:
        """Create an unverified test user."""
        user = User(
            id=uuid4(),
            email="unverified@example.com",
            hashed_password="hashed_password",
            full_name="Unverified User",
            global_role=GlobalRole.USER,
            is_active=True,
            email_verified=False,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.fixture
    async def verified_user(self, db_session: AsyncSession) -> User:
        """Create a verified test user."""
        user = User(
            id=uuid4(),
            email="verified@example.com",
            hashed_password="hashed_password",
            full_name="Verified User",
            global_role=GlobalRole.USER,
            is_active=True,
            email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    async def test_generate_and_send_verification_creates_token(
        self, db_session: AsyncSession, unverified_user: User
    ):
        """Test that generating verification creates a token and timestamp."""
        service = EmailVerificationService(db_session)

        # Mock the private backend attribute
        mock_backend = AsyncMock()
        mock_backend.send = AsyncMock(return_value=True)
        service._email_backend = mock_backend

        result = await service.generate_and_send_verification(
            user=unverified_user,
            locale="en",
            base_url="http://localhost:3000",
        )

        assert result is True
        assert unverified_user.email_verification_token is not None
        assert len(unverified_user.email_verification_token) == 64
        assert unverified_user.email_verification_sent_at is not None

    async def test_verify_token_success(
        self, db_session: AsyncSession, unverified_user: User
    ):
        """Test successful token verification."""
        service = EmailVerificationService(db_session)

        # Set up token
        test_token = "test_token_12345678901234567890123456789012345678901234"
        unverified_user.email_verification_token = test_token
        unverified_user.email_verification_sent_at = datetime.now(timezone.utc)
        await db_session.flush()

        # Verify
        result = await service.verify_token(test_token)

        assert result is not None
        assert result.id == unverified_user.id
        assert result.email_verified is True
        assert result.email_verification_token is None
        assert result.email_verification_sent_at is None

    async def test_verify_token_invalid_token(self, db_session: AsyncSession):
        """Test verification with invalid token."""
        service = EmailVerificationService(db_session)

        result = await service.verify_token("nonexistent_token")

        assert result is None

    async def test_verify_token_expired(
        self, db_session: AsyncSession, unverified_user: User
    ):
        """Test verification with expired token."""
        service = EmailVerificationService(db_session)

        # Set up expired token
        test_token = "expired_token_1234567890123456789012345678901234567890"
        unverified_user.email_verification_token = test_token
        unverified_user.email_verification_sent_at = datetime.now(timezone.utc) - timedelta(
            days=TOKEN_EXPIRATION_DAYS + 1
        )
        await db_session.flush()

        # Try to verify
        result = await service.verify_token(test_token)

        assert result is None
        # User should still be unverified
        assert unverified_user.email_verified is False

    async def test_can_resend_when_no_previous_send(
        self, db_session: AsyncSession, unverified_user: User
    ):
        """Test can_resend when no email has been sent yet."""
        service = EmailVerificationService(db_session)

        can_resend, seconds_remaining = service.can_resend(unverified_user)

        assert can_resend is True
        assert seconds_remaining == 0

    async def test_can_resend_during_cooldown(
        self, db_session: AsyncSession, unverified_user: User
    ):
        """Test can_resend during cooldown period."""
        service = EmailVerificationService(db_session)

        # Set recent send time
        unverified_user.email_verification_sent_at = datetime.now(timezone.utc) - timedelta(seconds=30)
        await db_session.flush()

        can_resend, seconds_remaining = service.can_resend(unverified_user)

        assert can_resend is False
        assert seconds_remaining > 0
        assert seconds_remaining <= RESEND_COOLDOWN_SECONDS

    async def test_can_resend_after_cooldown(
        self, db_session: AsyncSession, unverified_user: User
    ):
        """Test can_resend after cooldown period."""
        service = EmailVerificationService(db_session)

        # Set old send time
        unverified_user.email_verification_sent_at = datetime.now(timezone.utc) - timedelta(
            seconds=RESEND_COOLDOWN_SECONDS + 10
        )
        await db_session.flush()

        can_resend, seconds_remaining = service.can_resend(unverified_user)

        assert can_resend is True
        assert seconds_remaining == 0

    async def test_can_resend_verified_user(
        self, db_session: AsyncSession, verified_user: User
    ):
        """Test that verified users can't resend (returns False)."""
        service = EmailVerificationService(db_session)

        can_resend, seconds_remaining = service.can_resend(verified_user)

        assert can_resend is False
        assert seconds_remaining == 0

    async def test_verify_empty_token(self, db_session: AsyncSession):
        """Test verification with empty token."""
        service = EmailVerificationService(db_session)

        result = await service.verify_token("")
        assert result is None

        result = await service.verify_token(None)
        assert result is None

    async def test_get_user_by_token(
        self, db_session: AsyncSession, unverified_user: User
    ):
        """Test getting user by token without verifying."""
        service = EmailVerificationService(db_session)

        # Set up token
        test_token = "lookup_token_123456789012345678901234567890123456789012"
        unverified_user.email_verification_token = test_token
        await db_session.flush()

        # Get user
        result = await service.get_user_by_token(test_token)

        assert result is not None
        assert result.id == unverified_user.id
        # Should not modify verification status
        assert result.email_verified is False
        assert result.email_verification_token == test_token
