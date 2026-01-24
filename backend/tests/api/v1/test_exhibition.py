"""
Tests for Exhibition API endpoints.
"""
import pytest
from httpx import AsyncClient


class TestListExhibitions:
    """Tests for GET /api/v1/exhibitions/"""

    async def test_list_empty(self, client: AsyncClient):
        """Empty list returns 200 with empty array."""
        response = await client.get("/api/v1/exhibitions/")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_with_data(self, client: AsyncClient, test_organization: dict):
        """List returns created exhibitions."""
        # Create an exhibition first
        payload = {
            "title": "Test Convention",
            "slug": "test-convention",
            "start_date": "2026-06-15T09:00:00Z",
            "end_date": "2026-06-17T18:00:00Z",
            "organization_id": test_organization["id"],
        }
        await client.post("/api/v1/exhibitions/", json=payload)

        # List should contain it
        response = await client.get("/api/v1/exhibitions/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Convention"


class TestCreateExhibition:
    """Tests for POST /api/v1/exhibitions/"""

    async def test_create_success(self, client: AsyncClient, test_organization: dict):
        """Create returns 201 with created entity."""
        payload = {
            "title": "New Exhibition",
            "slug": "new-exhibition",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organization["id"],
            "city": "Paris",
            "country_code": "FR",
        }

        response = await client.post("/api/v1/exhibitions/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Exhibition"
        assert data["slug"] == "new-exhibition"
        assert data["city"] == "Paris"
        assert data["status"] == "DRAFT"
        assert "id" in data
        assert "created_at" in data

    async def test_create_duplicate_slug(
        self, client: AsyncClient, test_organization: dict
    ):
        """Duplicate slug returns 409 Conflict."""
        payload = {
            "title": "Exhibition 1",
            "slug": "same-slug",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organization["id"],
        }

        # Create first one
        response1 = await client.post("/api/v1/exhibitions/", json=payload)
        assert response1.status_code == 201

        # Try to create duplicate
        payload["title"] = "Exhibition 2"
        response2 = await client.post("/api/v1/exhibitions/", json=payload)

        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    async def test_create_validation_error(
        self, client: AsyncClient, test_organization: dict
    ):
        """Missing required field returns 422."""
        payload = {
            "slug": "missing-title",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organization["id"],
        }

        response = await client.post("/api/v1/exhibitions/", json=payload)

        assert response.status_code == 422


class TestGetExhibition:
    """Tests for GET /api/v1/exhibitions/{id}"""

    async def test_get_success(self, client: AsyncClient, test_organization: dict):
        """Get existing exhibition returns 200."""
        # Create first
        payload = {
            "title": "Get Test",
            "slug": "get-test",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organization["id"],
        }
        create_response = await client.post("/api/v1/exhibitions/", json=payload)
        exhibition_id = create_response.json()["id"]

        # Get it
        response = await client.get(f"/api/v1/exhibitions/{exhibition_id}")

        assert response.status_code == 200
        assert response.json()["title"] == "Get Test"

    async def test_get_not_found(self, client: AsyncClient):
        """Get non-existent exhibition returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(f"/api/v1/exhibitions/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Exhibition not found"


class TestUpdateExhibition:
    """Tests for PUT /api/v1/exhibitions/{id}"""

    async def test_update_success(self, client: AsyncClient, test_organization: dict):
        """Update returns 200 with updated entity."""
        # Create first
        payload = {
            "title": "Before Update",
            "slug": "update-test",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organization["id"],
        }
        create_response = await client.post("/api/v1/exhibitions/", json=payload)
        exhibition_id = create_response.json()["id"]

        # Update it
        update_payload = {
            "title": "After Update",
            "description": "Updated description",
            "status": "PUBLISHED",
        }
        response = await client.put(
            f"/api/v1/exhibitions/{exhibition_id}", json=update_payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "After Update"
        assert data["description"] == "Updated description"
        assert data["status"] == "PUBLISHED"
        assert data["slug"] == "update-test"  # Unchanged
        assert data["updated_at"] is not None

    async def test_update_not_found(self, client: AsyncClient):
        """Update non-existent exhibition returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.put(
            f"/api/v1/exhibitions/{fake_id}",
            json={"title": "Whatever"},
        )

        assert response.status_code == 404


class TestDeleteExhibition:
    """Tests for DELETE /api/v1/exhibitions/{id}"""

    async def test_delete_success(self, client: AsyncClient, test_organization: dict):
        """Delete returns 204 No Content."""
        # Create first
        payload = {
            "title": "To Delete",
            "slug": "delete-test",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organization["id"],
        }
        create_response = await client.post("/api/v1/exhibitions/", json=payload)
        exhibition_id = create_response.json()["id"]

        # Delete it
        response = await client.delete(f"/api/v1/exhibitions/{exhibition_id}")

        assert response.status_code == 204

        # Verify it's gone
        get_response = await client.get(f"/api/v1/exhibitions/{exhibition_id}")
        assert get_response.status_code == 404

    async def test_delete_not_found(self, client: AsyncClient):
        """Delete non-existent exhibition returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.delete(f"/api/v1/exhibitions/{fake_id}")

        assert response.status_code == 404
