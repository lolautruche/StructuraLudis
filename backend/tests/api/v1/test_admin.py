"""
Tests for Admin API endpoints.
"""
import pytest
from httpx import AsyncClient


class TestListUsers:
    """Tests for GET /api/v1/admin/users"""

    async def test_list_users_as_admin(
        self, admin_client: AsyncClient, test_organizer: dict, test_user: dict
    ):
        """Super admin can list all users."""
        response = await admin_client.get("/api/v1/admin/users")

        assert response.status_code == 200
        data = response.json()
        # Should have at least: super_admin, organizer, user
        assert len(data) >= 3

    async def test_list_users_filter_by_role(
        self, admin_client: AsyncClient, test_user: dict
    ):
        """Can filter users by role (#99)."""
        response = await admin_client.get(
            "/api/v1/admin/users", params={"role": "USER"}
        )

        assert response.status_code == 200
        data = response.json()
        assert all(u["global_role"] == "USER" for u in data)

    async def test_list_users_forbidden_for_non_admin(
        self, auth_client: AsyncClient
    ):
        """Non-admin users cannot access admin endpoints (#99)."""
        response = await auth_client.get("/api/v1/admin/users")

        assert response.status_code == 403
        assert "Admin" in response.json()["detail"]

    async def test_list_users_unauthorized(self, client: AsyncClient):
        """Unauthenticated request returns 401."""
        response = await client.get("/api/v1/admin/users")

        assert response.status_code == 401


class TestGetUser:
    """Tests for GET /api/v1/admin/users/{id}"""

    async def test_get_user_success(
        self, admin_client: AsyncClient, test_user: dict
    ):
        """Super admin can get user details."""
        response = await admin_client.get(f"/api/v1/admin/users/{test_user['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]

    async def test_get_user_not_found(self, admin_client: AsyncClient):
        """Returns 404 for non-existent user."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await admin_client.get(f"/api/v1/admin/users/{fake_id}")

        assert response.status_code == 404


class TestUpdateUserRole:
    """Tests for PATCH /api/v1/admin/users/{id}/role"""

    async def test_promote_to_admin(
        self, admin_client: AsyncClient, test_user: dict
    ):
        """Super admin can promote user to ADMIN (#99)."""
        response = await admin_client.patch(
            f"/api/v1/admin/users/{test_user['id']}/role",
            json={"global_role": "ADMIN"},
        )

        assert response.status_code == 200
        assert response.json()["global_role"] == "ADMIN"

    async def test_demote_to_user(
        self, admin_client: AsyncClient, test_organizer: dict
    ):
        """Super admin can demote organizer to USER."""
        response = await admin_client.patch(
            f"/api/v1/admin/users/{test_organizer['id']}/role",
            json={"global_role": "USER"},
        )

        assert response.status_code == 200
        assert response.json()["global_role"] == "USER"

    async def test_cannot_demote_self(
        self, admin_client: AsyncClient, test_super_admin: dict
    ):
        """Super admin cannot demote themselves."""
        response = await admin_client.patch(
            f"/api/v1/admin/users/{test_super_admin['id']}/role",
            json={"global_role": "USER"},
        )

        assert response.status_code == 400
        assert "yourself" in response.json()["detail"]

    async def test_promote_forbidden_for_non_admin(
        self, auth_client: AsyncClient, test_user: dict
    ):
        """Non-admin users cannot change roles (#99)."""
        response = await auth_client.patch(
            f"/api/v1/admin/users/{test_user['id']}/role",
            json={"global_role": "ADMIN"},
        )

        assert response.status_code == 403


class TestUpdateUserStatus:
    """Tests for PATCH /api/v1/admin/users/{id}/status"""

    async def test_deactivate_user(
        self, admin_client: AsyncClient, test_user: dict
    ):
        """Super admin can deactivate a user."""
        response = await admin_client.patch(
            f"/api/v1/admin/users/{test_user['id']}/status",
            json={"is_active": False},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    async def test_reactivate_user(
        self, admin_client: AsyncClient, test_user: dict
    ):
        """Super admin can reactivate a user."""
        # First deactivate
        await admin_client.patch(
            f"/api/v1/admin/users/{test_user['id']}/status",
            json={"is_active": False},
        )

        # Then reactivate
        response = await admin_client.patch(
            f"/api/v1/admin/users/{test_user['id']}/status",
            json={"is_active": True},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is True

    async def test_cannot_deactivate_self(
        self, admin_client: AsyncClient, test_super_admin: dict
    ):
        """Super admin cannot deactivate themselves."""
        response = await admin_client.patch(
            f"/api/v1/admin/users/{test_super_admin['id']}/status",
            json={"is_active": False},
        )

        assert response.status_code == 400
        assert "yourself" in response.json()["detail"]


class TestListAllExhibitions:
    """Tests for GET /api/v1/admin/exhibitions"""

    async def test_list_all_exhibitions(
        self, admin_client: AsyncClient, auth_client: AsyncClient, test_organizer: dict
    ):
        """Super admin can list all exhibitions."""
        # Create an exhibition first
        payload = {
            "title": "Admin List Test",
            "slug": "admin-list-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        await auth_client.post("/api/v1/exhibitions/", json=payload)

        response = await admin_client.get("/api/v1/admin/exhibitions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_list_exhibitions_forbidden_for_organizer(
        self, auth_client: AsyncClient
    ):
        """Organizer cannot access admin exhibitions list."""
        response = await auth_client.get("/api/v1/admin/exhibitions")

        assert response.status_code == 403


class TestPlatformStats:
    """Tests for GET /api/v1/admin/stats"""

    async def test_get_stats(
        self, admin_client: AsyncClient, test_organizer: dict, test_user: dict
    ):
        """Super admin can get platform statistics."""
        response = await admin_client.get("/api/v1/admin/stats")

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "exhibitions" in data
        assert "total" in data["users"]
        assert "by_role" in data["users"]

    async def test_stats_forbidden_for_organizer(self, auth_client: AsyncClient):
        """Organizer cannot access platform stats."""
        response = await auth_client.get("/api/v1/admin/stats")

        assert response.status_code == 403
