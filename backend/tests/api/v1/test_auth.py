"""
Tests for Authentication API endpoints.
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, create_access_token
from app.domain.user.entity import User
from app.domain.shared.entity import GlobalRole


class TestRegister:
    """Tests for POST /api/v1/auth/register"""

    async def test_register_success(self, client: AsyncClient):
        """Register a new user returns 201."""
        payload = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "full_name": "New User",
            "accept_privacy_policy": True,
        }

        response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["global_role"] == "USER"
        assert data["is_active"] is True
        assert "id" in data
        # Privacy policy consent timestamp should be set
        assert data["privacy_accepted_at"] is not None
        # Password should not be returned
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_register_without_privacy_consent_field(self, client: AsyncClient):
        """Register without accept_privacy_policy field returns 422."""
        payload = {
            "email": "noprivacy@example.com",
            "password": "securepassword123",
            "full_name": "No Privacy User",
            # Missing accept_privacy_policy
        }

        response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 422

    async def test_register_privacy_policy_rejected(self, client: AsyncClient):
        """Register with accept_privacy_policy=false returns 400."""
        payload = {
            "email": "rejected@example.com",
            "password": "securepassword123",
            "full_name": "Rejected User",
            "accept_privacy_policy": False,
        }

        response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 400
        assert "privacy policy" in response.json()["detail"].lower()

    async def test_register_duplicate_email(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Register with existing email returns 409."""
        # Create existing user
        user = User(
            id=uuid4(),
            email="existing@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Existing User",
            global_role=GlobalRole.USER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        payload = {
            "email": "existing@example.com",
            "password": "newpassword123",
            "accept_privacy_policy": True,
        }

        response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 409
        assert "already registered" in response.json()["detail"]

    async def test_register_invalid_email(self, client: AsyncClient):
        """Register with invalid email returns 422."""
        payload = {
            "email": "not-an-email",
            "password": "securepassword123",
            "accept_privacy_policy": True,
        }

        response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 422

    async def test_register_password_too_short(self, client: AsyncClient):
        """Register with password < 8 chars returns 422."""
        payload = {
            "email": "user@example.com",
            "password": "short",
            "accept_privacy_policy": True,
        }

        response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/v1/auth/login"""

    async def test_login_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Login with valid credentials returns JWT token."""
        # Create user with known password
        password = "correctpassword123"
        user = User(
            id=uuid4(),
            email="login@example.com",
            hashed_password=get_password_hash(password),
            full_name="Login User",
            global_role=GlobalRole.USER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        payload = {
            "email": "login@example.com",
            "password": password,
        }

        response = await client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Login with wrong password returns 401."""
        user = User(
            id=uuid4(),
            email="wrongpass@example.com",
            hashed_password=get_password_hash("correctpassword"),
            full_name="Wrong Pass User",
            global_role=GlobalRole.USER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        payload = {
            "email": "wrongpass@example.com",
            "password": "wrongpassword",
        }

        response = await client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Login with non-existent email returns 401."""
        payload = {
            "email": "nonexistent@example.com",
            "password": "anypassword",
        }

        response = await client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 401

    async def test_login_inactive_user(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Login with inactive user returns 403 with specific message."""
        password = "password123"
        user = User(
            id=uuid4(),
            email="inactive@example.com",
            hashed_password=get_password_hash(password),
            full_name="Inactive User",
            global_role=GlobalRole.USER,
            is_active=False,  # Inactive
        )
        db_session.add(user)
        await db_session.commit()

        payload = {
            "email": "inactive@example.com",
            "password": password,
        }

        response = await client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 403
        assert response.json()["detail"] == "Account deactivated"


class TestJWTAuthentication:
    """Tests for JWT token authentication."""

    async def test_access_protected_route_with_jwt(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Access protected route with valid JWT succeeds."""
        # Create user
        user = User(
            id=uuid4(),
            email="jwt@example.com",
            hashed_password=get_password_hash("password"),
            full_name="JWT User",
            global_role=GlobalRole.USER,  # Regular user (#99)
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Create token
        token = create_access_token(subject=str(user.id))

        # Access protected route
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Regular USER doesn't have admin access, but auth should pass
        # (will get 403, not 401)
        assert response.status_code == 403

    async def test_access_protected_route_with_invalid_jwt(
        self, client: AsyncClient
    ):
        """Access protected route with invalid JWT returns 401."""
        response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    async def test_access_protected_route_without_auth(
        self, client: AsyncClient
    ):
        """Access protected route without auth returns 401."""
        response = await client.get("/api/v1/admin/users")

        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

    async def test_full_auth_flow(
        self, client: AsyncClient
    ):
        """Test complete registration -> login -> access protected route flow."""
        # Register
        register_payload = {
            "email": "flow@example.com",
            "password": "securepassword123",
            "full_name": "Flow User",
            "accept_privacy_policy": True,
        }
        register_resp = await client.post("/api/v1/auth/register", json=register_payload)
        assert register_resp.status_code == 201

        # Login
        login_payload = {
            "email": "flow@example.com",
            "password": "securepassword123",
        }
        login_resp = await client.post("/api/v1/auth/login", json=login_payload)
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        # Access protected route (list organizations - should work)
        orgs_resp = await client.get(
            "/api/v1/organizations/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert orgs_resp.status_code == 200


class TestEmailVerification:
    """Tests for email verification endpoints."""

    async def test_register_sends_verification_email(self, client: AsyncClient):
        """Register creates user with unverified email and sends verification."""
        payload = {
            "email": "needsverify@example.com",
            "password": "securepassword123",
            "full_name": "Needs Verify",
            "accept_privacy_policy": True,
        }

        response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 201
        data = response.json()
        # New users should have email_verified = False
        assert data["email_verified"] is False

    async def test_verify_email_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Verify email with valid token succeeds."""
        # Create user with verification token
        test_token = "valid_token_12345678901234567890123456789012345678901234"
        user = User(
            id=uuid4(),
            email="toverify@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="To Verify",
            global_role=GlobalRole.USER,
            is_active=True,
            email_verified=False,
            email_verification_token=test_token,
            email_verification_sent_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.get(f"/api/v1/auth/verify-email?token={test_token}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Refresh user to check update
        await db_session.refresh(user)
        assert user.email_verified is True
        assert user.email_verification_token is None

    async def test_verify_email_invalid_token(self, client: AsyncClient):
        """Verify email with invalid token returns 400."""
        response = await client.get("/api/v1/auth/verify-email?token=invalid_token")

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    async def test_verify_email_expired_token(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Verify email with expired token returns 400."""
        # Create user with expired token
        test_token = "expired_token_123456789012345678901234567890123456789012"
        user = User(
            id=uuid4(),
            email="expired@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Expired Token",
            global_role=GlobalRole.USER,
            is_active=True,
            email_verified=False,
            email_verification_token=test_token,
            email_verification_sent_at=datetime.now(timezone.utc) - timedelta(days=8),
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.get(f"/api/v1/auth/verify-email?token={test_token}")

        assert response.status_code == 400

    async def test_resend_verification_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Resend verification email succeeds for unverified user."""
        # Create unverified user
        user = User(
            id=uuid4(),
            email="resend@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Resend User",
            global_role=GlobalRole.USER,
            is_active=True,
            email_verified=False,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/resend-verification",
            headers={"X-User-ID": str(user.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Check token was set
        await db_session.refresh(user)
        assert user.email_verification_token is not None
        assert user.email_verification_sent_at is not None

    async def test_resend_verification_already_verified(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Resend verification returns success=False for verified user."""
        # Create verified user
        user = User(
            id=uuid4(),
            email="alreadyverified@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Already Verified",
            global_role=GlobalRole.USER,
            is_active=True,
            email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/resend-verification",
            headers={"X-User-ID": str(user.id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "already verified" in data["message"].lower()

    async def test_resend_verification_rate_limited(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Resend verification is rate limited (60s cooldown)."""
        # Create user with recent verification send
        user = User(
            id=uuid4(),
            email="ratelimited@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Rate Limited",
            global_role=GlobalRole.USER,
            is_active=True,
            email_verified=False,
            email_verification_token="existing_token_12345678901234567890123456789012",
            email_verification_sent_at=datetime.now(timezone.utc) - timedelta(seconds=30),
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/resend-verification",
            headers={"X-User-ID": str(user.id)},
        )

        assert response.status_code == 429
        assert "Retry-After" in response.headers

    async def test_resend_verification_requires_auth(self, client: AsyncClient):
        """Resend verification requires authentication."""
        response = await client.post("/api/v1/auth/resend-verification")

        assert response.status_code == 401

    async def test_login_allowed_without_verification(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Login is allowed even if email is not verified."""
        password = "password123"
        user = User(
            id=uuid4(),
            email="unverified_login@example.com",
            hashed_password=get_password_hash(password),
            full_name="Unverified Login",
            global_role=GlobalRole.USER,
            is_active=True,
            email_verified=False,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": password},
        )

        assert response.status_code == 200
        assert "access_token" in response.json()


class TestRememberMe:
    """Tests for remember_me functionality."""

    async def test_login_with_remember_me_returns_longer_token(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Login with remember_me=true returns token with 30 day expiration."""
        import base64
        import json

        password = "password123"
        user = User(
            id=uuid4(),
            email="remember@example.com",
            hashed_password=get_password_hash(password),
            full_name="Remember User",
            global_role=GlobalRole.USER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": password, "remember_me": True},
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        # Decode token payload to check expiration
        payload_b64 = token.split(".")[1]
        # Add padding
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        # Token should expire in ~30 days (allow some margin)
        exp_delta = payload["exp"] - payload["iat"]
        days = exp_delta / (60 * 60 * 24)
        assert 29 <= days <= 31  # Should be ~30 days

    async def test_login_without_remember_me_returns_standard_token(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Login without remember_me returns token with standard expiration (24h)."""
        import base64
        import json

        password = "password123"
        user = User(
            id=uuid4(),
            email="noremember@example.com",
            hashed_password=get_password_hash(password),
            full_name="No Remember User",
            global_role=GlobalRole.USER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": password},
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        # Decode token payload to check expiration
        payload_b64 = token.split(".")[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        # Token should expire in ~24 hours (allow some margin)
        exp_delta = payload["exp"] - payload["iat"]
        hours = exp_delta / (60 * 60)
        assert 23 <= hours <= 25  # Should be ~24 hours


class TestForgotPassword:
    """Tests for forgot password functionality."""

    async def test_forgot_password_existing_user(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Forgot password for existing user returns success and sets token."""
        user = User(
            id=uuid4(),
            email="forgot@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Forgot User",
            global_role=GlobalRole.USER,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "forgot@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Check token was set
        await db_session.refresh(user)
        assert user.password_reset_token is not None
        assert user.password_reset_sent_at is not None

    async def test_forgot_password_nonexistent_user(self, client: AsyncClient):
        """Forgot password for non-existent email still returns success (prevent enumeration)."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_forgot_password_invalid_email_format(self, client: AsyncClient):
        """Forgot password with invalid email format returns 422."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "not-an-email"},
        )

        assert response.status_code == 422


class TestResetPassword:
    """Tests for reset password functionality."""

    async def test_reset_password_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Reset password with valid token succeeds."""
        test_token = "reset_token_123456789012345678901234567890123456789012345"
        user = User(
            id=uuid4(),
            email="reset@example.com",
            hashed_password=get_password_hash("oldpassword123"),
            full_name="Reset User",
            global_role=GlobalRole.USER,
            is_active=True,
            password_reset_token=test_token,
            password_reset_sent_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": test_token, "new_password": "newpassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Check password was changed and token cleared
        await db_session.refresh(user)
        assert user.password_reset_token is None
        assert user.password_reset_sent_at is None

        # Verify can login with new password
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "reset@example.com", "password": "newpassword123"},
        )
        assert login_response.status_code == 200

    async def test_reset_password_invalid_token(self, client: AsyncClient):
        """Reset password with invalid token returns 400."""
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": "invalid_token", "new_password": "newpassword123"},
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    async def test_reset_password_expired_token(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Reset password with expired token returns 400."""
        test_token = "expired_reset_token_12345678901234567890123456789012345"
        user = User(
            id=uuid4(),
            email="expired_reset@example.com",
            hashed_password=get_password_hash("oldpassword123"),
            full_name="Expired Reset User",
            global_role=GlobalRole.USER,
            is_active=True,
            password_reset_token=test_token,
            password_reset_sent_at=datetime.now(timezone.utc) - timedelta(hours=2),  # Expired (> 1 hour)
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": test_token, "new_password": "newpassword123"},
        )

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    async def test_reset_password_too_short(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Reset password with password < 8 chars returns 422."""
        test_token = "short_pass_token_123456789012345678901234567890123456"
        user = User(
            id=uuid4(),
            email="shortpass@example.com",
            hashed_password=get_password_hash("oldpassword123"),
            full_name="Short Pass User",
            global_role=GlobalRole.USER,
            is_active=True,
            password_reset_token=test_token,
            password_reset_sent_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": test_token, "new_password": "short"},
        )

        assert response.status_code == 422