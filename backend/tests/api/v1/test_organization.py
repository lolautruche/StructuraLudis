"""
Tests for Organization API endpoints.
"""
import pytest
from httpx import AsyncClient


class TestListOrganizations:
    """Tests for GET /api/v1/organizations/"""

    async def test_list_empty(self, client: AsyncClient):
        """Empty list returns 200 with empty array."""
        response = await client.get("/api/v1/organizations/")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_with_data(self, client: AsyncClient):
        """List returns created organizations."""
        payload = {
            "name": "Test Org",
            "slug": "test-org",
            "contact_email": "test@example.com",
        }
        await client.post("/api/v1/organizations/", json=payload)

        response = await client.get("/api/v1/organizations/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Org"


class TestCreateOrganization:
    """Tests for POST /api/v1/organizations/"""

    async def test_create_success(self, client: AsyncClient):
        """Create returns 201 with created entity."""
        payload = {
            "name": "Convention JdR France",
            "slug": "conv-jdr-france",
            "contact_email": "contact@convjdr.fr",
            "legal_registration_number": "SIRET123456",
        }

        response = await client.post("/api/v1/organizations/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Convention JdR France"
        assert data["slug"] == "conv-jdr-france"
        assert data["contact_email"] == "contact@convjdr.fr"
        assert "id" in data
        assert "created_at" in data

    async def test_create_minimal(self, client: AsyncClient):
        """Create with only required fields."""
        payload = {
            "name": "Minimal Org",
            "slug": "minimal-org",
        }

        response = await client.post("/api/v1/organizations/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Org"
        assert data["contact_email"] is None

    async def test_create_duplicate_slug(self, client: AsyncClient):
        """Duplicate slug returns 409 Conflict."""
        payload = {
            "name": "Org 1",
            "slug": "same-slug",
        }

        response1 = await client.post("/api/v1/organizations/", json=payload)
        assert response1.status_code == 201

        payload["name"] = "Org 2"
        response2 = await client.post("/api/v1/organizations/", json=payload)

        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    async def test_create_invalid_slug(self, client: AsyncClient):
        """Invalid slug format returns 422."""
        payload = {
            "name": "Bad Slug Org",
            "slug": "Invalid Slug!",  # Spaces and special chars not allowed
        }

        response = await client.post("/api/v1/organizations/", json=payload)

        assert response.status_code == 422

    async def test_create_invalid_email(self, client: AsyncClient):
        """Invalid email format returns 422."""
        payload = {
            "name": "Bad Email Org",
            "slug": "bad-email-org",
            "contact_email": "not-an-email",
        }

        response = await client.post("/api/v1/organizations/", json=payload)

        assert response.status_code == 422


class TestGetOrganization:
    """Tests for GET /api/v1/organizations/{id}"""

    async def test_get_success(self, client: AsyncClient):
        """Get existing organization returns 200."""
        payload = {
            "name": "Get Test",
            "slug": "get-test",
        }
        create_response = await client.post("/api/v1/organizations/", json=payload)
        org_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/organizations/{org_id}")

        assert response.status_code == 200
        assert response.json()["name"] == "Get Test"

    async def test_get_not_found(self, client: AsyncClient):
        """Get non-existent organization returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(f"/api/v1/organizations/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Organization not found"


class TestUpdateOrganization:
    """Tests for PUT /api/v1/organizations/{id}"""

    async def test_update_success(self, client: AsyncClient):
        """Update returns 200 with updated entity."""
        payload = {
            "name": "Before Update",
            "slug": "update-test",
        }
        create_response = await client.post("/api/v1/organizations/", json=payload)
        org_id = create_response.json()["id"]

        update_payload = {
            "name": "After Update",
            "contact_email": "new@example.com",
        }
        response = await client.put(
            f"/api/v1/organizations/{org_id}", json=update_payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "After Update"
        assert data["contact_email"] == "new@example.com"
        assert data["slug"] == "update-test"  # Unchanged
        assert data["updated_at"] is not None

    async def test_update_not_found(self, client: AsyncClient):
        """Update non-existent organization returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.put(
            f"/api/v1/organizations/{fake_id}",
            json={"name": "Whatever"},
        )

        assert response.status_code == 404


class TestDeleteOrganization:
    """Tests for DELETE /api/v1/organizations/{id}"""

    async def test_delete_success(self, client: AsyncClient):
        """Delete returns 204 No Content."""
        payload = {
            "name": "To Delete",
            "slug": "delete-test",
        }
        create_response = await client.post("/api/v1/organizations/", json=payload)
        org_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/organizations/{org_id}")

        assert response.status_code == 204

        get_response = await client.get(f"/api/v1/organizations/{org_id}")
        assert get_response.status_code == 404

    async def test_delete_not_found(self, client: AsyncClient):
        """Delete non-existent organization returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.delete(f"/api/v1/organizations/{fake_id}")

        assert response.status_code == 404
