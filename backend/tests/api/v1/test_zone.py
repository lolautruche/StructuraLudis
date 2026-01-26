"""
Tests for Zone API endpoints.
"""
import pytest
from httpx import AsyncClient


class TestListZones:
    """Tests for GET /api/v1/zones/"""

    async def test_list_empty(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Empty list returns 200 with empty array."""
        # Create exhibition first
        exhibition_payload = {
            "title": "Zone List Test",
            "slug": "zone-list-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        response = await auth_client.get(
            "/api/v1/zones/", params={"exhibition_id": exhibition_id}
        )

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_with_data(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """List returns created zones."""
        # Create exhibition
        exhibition_payload = {
            "title": "Zone List Data Test",
            "slug": "zone-list-data",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create zones
        for name in ["Alpha Hall", "Beta Hall"]:
            zone_payload = {
                "name": name,
                "exhibition_id": exhibition_id,
                "type": "MIXED",
            }
            await auth_client.post("/api/v1/zones/", json=zone_payload)

        response = await auth_client.get(
            "/api/v1/zones/", params={"exhibition_id": exhibition_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Ordered by name
        assert data[0]["name"] == "Alpha Hall"
        assert data[1]["name"] == "Beta Hall"


class TestCreateZone:
    """Tests for POST /api/v1/zones/"""

    async def test_create_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Create returns 201 with created entity."""
        # Create exhibition first
        exhibition_payload = {
            "title": "Zone Create Test",
            "slug": "zone-create-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {
            "name": "Main Hall",
            "description": "The main gaming area",
            "exhibition_id": exhibition_id,
            "type": "MIXED",
        }

        response = await auth_client.post("/api/v1/zones/", json=zone_payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Main Hall"
        assert data["description"] == "The main gaming area"
        assert data["type"] == "MIXED"
        assert data["exhibition_id"] == exhibition_id
        assert "id" in data
        assert "created_at" in data

    async def test_create_unauthorized(self, client: AsyncClient):
        """Create without auth returns 401."""
        zone_payload = {
            "name": "Unauthorized Zone",
            "exhibition_id": "00000000-0000-0000-0000-000000000000",
        }

        response = await client.post("/api/v1/zones/", json=zone_payload)

        assert response.status_code == 401

    async def test_create_forbidden_user_role(
        self, auth_client: AsyncClient, client: AsyncClient, test_user: dict, test_organizer: dict
    ):
        """Create with USER role returns 403."""
        # Create a real exhibition first
        exhibition_payload = {
            "title": "Forbidden Zone Test",
            "slug": "forbidden-zone-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {
            "name": "Forbidden Zone",
            "exhibition_id": exhibition_id,
        }

        response = await client.post(
            "/api/v1/zones/",
            json=zone_payload,
            headers={"X-User-ID": test_user["id"]},
        )

        # Will return 403 (forbidden) because USER role cannot create zones
        assert response.status_code == 403

    async def test_create_exhibition_not_found(
        self, auth_client: AsyncClient
    ):
        """Create with non-existent exhibition returns 404."""
        zone_payload = {
            "name": "Orphan Zone",
            "exhibition_id": "00000000-0000-0000-0000-000000000000",
        }

        response = await auth_client.post("/api/v1/zones/", json=zone_payload)

        assert response.status_code == 404
        assert "Exhibition not found" in response.json()["detail"]

    async def test_create_with_delegation(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Create zone with delegation to group."""
        # Create exhibition
        exhibition_payload = {
            "title": "Delegation Test",
            "slug": "delegation-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {
            "name": "Partner Zone",
            "exhibition_id": exhibition_id,
            "delegated_to_group_id": test_organizer["group_id"],
        }

        response = await auth_client.post("/api/v1/zones/", json=zone_payload)

        assert response.status_code == 201
        data = response.json()
        assert data["delegated_to_group_id"] == test_organizer["group_id"]


class TestGetZone:
    """Tests for GET /api/v1/zones/{zone_id}"""

    async def test_get_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Get existing zone returns 200."""
        # Create exhibition and zone
        exhibition_payload = {
            "title": "Get Zone Test",
            "slug": "get-zone-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {
            "name": "Test Zone",
            "exhibition_id": exhibition_id,
        }
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        # Get it (no auth required for read)
        response = await auth_client.get(f"/api/v1/zones/{zone_id}")

        assert response.status_code == 200
        assert response.json()["name"] == "Test Zone"

    async def test_get_not_found(self, client: AsyncClient):
        """Get non-existent zone returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(f"/api/v1/zones/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Zone not found"


class TestListTables:
    """Tests for GET /api/v1/zones/{zone_id}/tables"""

    async def test_list_empty(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Empty list returns 200 with empty array."""
        # Create exhibition and zone
        exhibition_payload = {
            "title": "Tables List Test",
            "slug": "tables-list-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {"name": "Empty Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        response = await auth_client.get(f"/api/v1/zones/{zone_id}/tables")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_with_data(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """List returns created tables."""
        # Create exhibition and zone
        exhibition_payload = {
            "title": "Tables Data Test",
            "slug": "tables-data-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {"name": "Tables Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        # Create tables
        tables_payload = {
            "prefix": "T",
            "count": 5,
            "starting_number": 1,
            "capacity": 4,
        }
        await auth_client.post(f"/api/v1/zones/{zone_id}/batch-tables", json=tables_payload)

        response = await auth_client.get(f"/api/v1/zones/{zone_id}/tables")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        # Ordered by label
        assert data[0]["label"] == "T1"
        assert data[4]["label"] == "T5"

    async def test_list_zone_not_found(self, client: AsyncClient):
        """List tables for non-existent zone returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(f"/api/v1/zones/{fake_id}/tables")

        assert response.status_code == 404


class TestBatchCreateTables:
    """Tests for POST /api/v1/zones/{zone_id}/batch-tables"""

    async def test_batch_create_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Batch create returns 201 with created tables."""
        # Create exhibition and zone
        exhibition_payload = {
            "title": "Batch Tables Test",
            "slug": "batch-tables-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {"name": "Batch Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        tables_payload = {
            "prefix": "Table ",
            "count": 10,
            "starting_number": 1,
            "capacity": 6,
        }

        response = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables", json=tables_payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["created_count"] == 10
        assert len(data["tables"]) == 10
        assert data["tables"][0]["label"] == "Table 1"
        assert data["tables"][9]["label"] == "Table 10"
        assert all(t["capacity"] == 6 for t in data["tables"])
        assert all(t["status"] == "AVAILABLE" for t in data["tables"])

    async def test_batch_create_custom_start(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Batch create with custom starting number."""
        # Create exhibition and zone
        exhibition_payload = {
            "title": "Custom Start Test",
            "slug": "custom-start-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {"name": "Custom Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        tables_payload = {
            "prefix": "VIP-",
            "count": 3,
            "starting_number": 100,
            "capacity": 8,
        }

        response = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables", json=tables_payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["tables"][0]["label"] == "VIP-100"
        assert data["tables"][1]["label"] == "VIP-101"
        assert data["tables"][2]["label"] == "VIP-102"

    async def test_batch_create_duplicate_labels(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Batch create with duplicate labels returns 409."""
        # Create exhibition and zone
        exhibition_payload = {
            "title": "Duplicate Labels Test",
            "slug": "duplicate-labels-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {"name": "Dup Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        # Create first batch
        tables_payload = {"prefix": "T", "count": 5, "starting_number": 1}
        resp1 = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables", json=tables_payload
        )
        assert resp1.status_code == 201

        # Try to create overlapping batch
        tables_payload = {"prefix": "T", "count": 5, "starting_number": 3}
        resp2 = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables", json=tables_payload
        )

        assert resp2.status_code == 409
        assert "already exists" in resp2.json()["detail"]

    async def test_batch_create_zone_not_found(
        self, auth_client: AsyncClient
    ):
        """Batch create for non-existent zone returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        tables_payload = {"prefix": "T", "count": 5}

        response = await auth_client.post(
            f"/api/v1/zones/{fake_id}/batch-tables", json=tables_payload
        )

        assert response.status_code == 404

    async def test_batch_create_unauthorized(self, client: AsyncClient):
        """Batch create without auth returns 401."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        tables_payload = {"prefix": "T", "count": 5}

        response = await client.post(
            f"/api/v1/zones/{fake_id}/batch-tables", json=tables_payload
        )

        assert response.status_code == 401

    async def test_batch_create_forbidden_user_role(
        self, auth_client: AsyncClient, client: AsyncClient, test_user: dict, test_organizer: dict
    ):
        """Batch create with USER role returns 403."""
        # Create exhibition and zone first
        exhibition_payload = {
            "title": "Forbidden Batch Test",
            "slug": "forbidden-batch-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {"name": "Forbidden Batch Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        tables_payload = {"prefix": "T", "count": 5}

        response = await client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json=tables_payload,
            headers={"X-User-ID": test_user["id"]},
        )

        # Will return 403 (forbidden) because USER role cannot manage zones
        assert response.status_code == 403
