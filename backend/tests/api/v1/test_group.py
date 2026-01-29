"""
Tests for Group API endpoints (#31).
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.organization.entity import UserGroup
from app.domain.user.entity import UserGroupMembership
from app.domain.shared.entity import UserGroupType, GroupRole


class TestListGroups:
    """Tests for GET /api/v1/groups/"""

    async def test_list_empty(self, client: AsyncClient):
        """Empty list returns 200 with empty array."""
        response = await client.get("/api/v1/groups/")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_with_filter(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """List filters by organization_id."""
        # Create a group
        group_payload = {
            "name": "Test Partner Group",
            "organization_id": test_organizer["organization_id"],
            "type": "ASSOCIATION",
        }
        await auth_client.post("/api/v1/groups/", json=group_payload)

        # List with filter
        response = await auth_client.get(
            f"/api/v1/groups/?organization_id={test_organizer['organization_id']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2  # Staff group + our new group
        group_names = [g["name"] for g in data]
        assert "Test Partner Group" in group_names


class TestCreateGroup:
    """Tests for POST /api/v1/groups/"""

    async def test_create_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Organizer can create a group."""
        payload = {
            "name": "New Partner Group",
            "organization_id": test_organizer["organization_id"],
            "type": "EXHIBITOR",
            "is_public": True,
        }

        response = await auth_client.post("/api/v1/groups/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Partner Group"
        assert data["type"] == "EXHIBITOR"
        assert data["is_public"] is True

    async def test_create_forbidden_for_user(
        self, client: AsyncClient, test_user: dict, test_organization: dict
    ):
        """Regular user cannot create groups."""
        payload = {
            "name": "Forbidden Group",
            "organization_id": test_organization["id"],
            "type": "ASSOCIATION",
        }

        response = await client.post(
            "/api/v1/groups/",
            json=payload,
            headers={"X-User-ID": test_user["id"]},
        )

        assert response.status_code == 403


class TestGroupMembers:
    """Tests for group member management endpoints."""

    @pytest.fixture
    async def test_group(
        self, auth_client: AsyncClient, test_organizer: dict
    ) -> dict:
        """Create a test group."""
        payload = {
            "name": "Member Test Group",
            "organization_id": test_organizer["organization_id"],
            "type": "ASSOCIATION",
        }
        response = await auth_client.post("/api/v1/groups/", json=payload)
        return response.json()

    async def test_add_member(
        self,
        auth_client: AsyncClient,
        test_group: dict,
        test_user: dict,
    ):
        """Organizer can add a member to a group."""
        response = await auth_client.post(
            f"/api/v1/groups/{test_group['id']}/members",
            json={"user_id": test_user["id"], "group_role": "MEMBER"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == test_user["id"]
        assert data["group_role"] == "MEMBER"
        assert "user_email" in data

    async def test_add_member_already_exists(
        self,
        auth_client: AsyncClient,
        test_group: dict,
        test_user: dict,
    ):
        """Cannot add same member twice."""
        # Add first time
        await auth_client.post(
            f"/api/v1/groups/{test_group['id']}/members",
            json={"user_id": test_user["id"], "group_role": "MEMBER"},
        )

        # Try to add again
        response = await auth_client.post(
            f"/api/v1/groups/{test_group['id']}/members",
            json={"user_id": test_user["id"], "group_role": "ADMIN"},
        )

        assert response.status_code == 409

    async def test_list_members(
        self,
        auth_client: AsyncClient,
        test_group: dict,
        test_user: dict,
    ):
        """List group members."""
        # Add a member
        await auth_client.post(
            f"/api/v1/groups/{test_group['id']}/members",
            json={"user_id": test_user["id"], "group_role": "MEMBER"},
        )

        # List members
        response = await auth_client.get(
            f"/api/v1/groups/{test_group['id']}/members"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == test_user["id"]

    async def test_update_member_role(
        self,
        auth_client: AsyncClient,
        test_group: dict,
        test_user: dict,
    ):
        """Update a member's role."""
        # Add as member
        await auth_client.post(
            f"/api/v1/groups/{test_group['id']}/members",
            json={"user_id": test_user["id"], "group_role": "MEMBER"},
        )

        # Promote to admin
        response = await auth_client.patch(
            f"/api/v1/groups/{test_group['id']}/members/{test_user['id']}",
            json={"group_role": "ADMIN"},
        )

        assert response.status_code == 200
        assert response.json()["group_role"] == "ADMIN"

    async def test_remove_member(
        self,
        auth_client: AsyncClient,
        test_group: dict,
        test_user: dict,
    ):
        """Remove a member from group."""
        # Add member
        await auth_client.post(
            f"/api/v1/groups/{test_group['id']}/members",
            json={"user_id": test_user["id"], "group_role": "MEMBER"},
        )

        # Remove
        response = await auth_client.delete(
            f"/api/v1/groups/{test_group['id']}/members/{test_user['id']}"
        )

        assert response.status_code == 204

        # Verify removed
        members_resp = await auth_client.get(
            f"/api/v1/groups/{test_group['id']}/members"
        )
        assert len(members_resp.json()) == 0

    async def test_self_removal(
        self,
        auth_client: AsyncClient,
        client: AsyncClient,
        test_group: dict,
        test_user: dict,
    ):
        """Member can remove themselves from group."""
        # Add member
        await auth_client.post(
            f"/api/v1/groups/{test_group['id']}/members",
            json={"user_id": test_user["id"], "group_role": "MEMBER"},
        )

        # Self-remove
        response = await client.delete(
            f"/api/v1/groups/{test_group['id']}/members/{test_user['id']}",
            headers={"X-User-ID": test_user["id"]},
        )

        assert response.status_code == 204

    async def test_cannot_remove_last_owner(
        self,
        auth_client: AsyncClient,
        test_group: dict,
        test_organizer: dict,
    ):
        """Cannot remove the last owner of a group."""
        # Add organizer as owner
        await auth_client.post(
            f"/api/v1/groups/{test_group['id']}/members",
            json={"user_id": test_organizer["user_id"], "group_role": "OWNER"},
        )

        # Try to remove
        response = await auth_client.delete(
            f"/api/v1/groups/{test_group['id']}/members/{test_organizer['user_id']}"
        )

        assert response.status_code == 400
        assert "last owner" in response.json()["detail"]

    async def test_cannot_demote_last_owner(
        self,
        auth_client: AsyncClient,
        test_group: dict,
        test_organizer: dict,
    ):
        """Cannot demote the last owner to member."""
        # Add organizer as owner
        await auth_client.post(
            f"/api/v1/groups/{test_group['id']}/members",
            json={"user_id": test_organizer["user_id"], "group_role": "OWNER"},
        )

        # Try to demote
        response = await auth_client.patch(
            f"/api/v1/groups/{test_group['id']}/members/{test_organizer['user_id']}",
            json={"group_role": "MEMBER"},
        )

        assert response.status_code == 400
        assert "last owner" in response.json()["detail"]


class TestGroupPermissions:
    """Tests for group-based permissions."""

    @pytest.fixture
    async def group_with_admin(
        self,
        auth_client: AsyncClient,
        test_organizer: dict,
        test_user: dict,
    ) -> dict:
        """Create a group with test_user as admin."""
        # Create group
        payload = {
            "name": "Permission Test Group",
            "organization_id": test_organizer["organization_id"],
            "type": "ASSOCIATION",
        }
        group_resp = await auth_client.post("/api/v1/groups/", json=payload)
        group = group_resp.json()

        # Add test_user as admin
        await auth_client.post(
            f"/api/v1/groups/{group['id']}/members",
            json={"user_id": test_user["id"], "group_role": "ADMIN"},
        )

        return group

    async def test_group_admin_can_add_members(
        self,
        client: AsyncClient,
        group_with_admin: dict,
        test_user: dict,
        second_test_user: dict,
    ):
        """Group admin can add new members."""
        response = await client.post(
            f"/api/v1/groups/{group_with_admin['id']}/members",
            json={"user_id": second_test_user["id"], "group_role": "MEMBER"},
            headers={"X-User-ID": test_user["id"]},
        )

        assert response.status_code == 201

    async def test_regular_member_cannot_add_members(
        self,
        client: AsyncClient,
        auth_client: AsyncClient,
        test_organizer: dict,
        test_user: dict,
        second_test_user: dict,
    ):
        """Regular member cannot add new members."""
        # Create group
        payload = {
            "name": "No Permission Group",
            "organization_id": test_organizer["organization_id"],
            "type": "ASSOCIATION",
        }
        group_resp = await auth_client.post("/api/v1/groups/", json=payload)
        group = group_resp.json()

        # Add test_user as regular member
        await auth_client.post(
            f"/api/v1/groups/{group['id']}/members",
            json={"user_id": test_user["id"], "group_role": "MEMBER"},
        )

        # Try to add another member as regular member
        response = await client.post(
            f"/api/v1/groups/{group['id']}/members",
            json={"user_id": second_test_user["id"], "group_role": "MEMBER"},
            headers={"X-User-ID": test_user["id"]},
        )

        assert response.status_code == 403