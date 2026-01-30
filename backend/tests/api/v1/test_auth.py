"""
Tests for Authentication API endpoints.
"""
import pytest
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
        """Login with inactive user returns 401."""
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

        assert response.status_code == 401


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
            global_role=GlobalRole.ORGANIZER,
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

        # ORGANIZER doesn't have admin access, but auth should pass
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