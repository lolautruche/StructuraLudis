"""
Tests for Zone API endpoints.
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user.entity import User, UserGroupMembership, UserExhibitionRole
from app.domain.organization.entity import UserGroup
from app.domain.shared.entity import GlobalRole, ExhibitionRole, UserGroupType, GroupRole


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


class TestZoneTablePrefix:
    """Tests for zone table_prefix feature (#93)."""

    async def test_create_zone_with_table_prefix(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Create zone with table_prefix returns 201."""
        # Create exhibition
        exhibition_payload = {
            "title": "Table Prefix Test",
            "slug": "table-prefix-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {
            "name": "RPG Zone",
            "exhibition_id": exhibition_id,
            "table_prefix": "JDR-",
        }

        response = await auth_client.post("/api/v1/zones/", json=zone_payload)

        assert response.status_code == 201
        data = response.json()
        assert data["table_prefix"] == "JDR-"

    async def test_batch_create_uses_zone_prefix(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Batch create without prefix uses zone's table_prefix."""
        # Create exhibition
        exhibition_payload = {
            "title": "Zone Prefix Batch Test",
            "slug": "zone-prefix-batch-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create zone with prefix
        zone_payload = {
            "name": "RPG Zone",
            "exhibition_id": exhibition_id,
            "table_prefix": "RPG-",
        }
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        # Create tables WITHOUT specifying prefix
        tables_payload = {"count": 3}

        response = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables", json=tables_payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["tables"][0]["label"] == "RPG-1"
        assert data["tables"][1]["label"] == "RPG-2"
        assert data["tables"][2]["label"] == "RPG-3"

    async def test_batch_create_auto_starting_number(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Batch create without starting_number auto-continues from highest."""
        # Create exhibition
        exhibition_payload = {
            "title": "Auto Start Test",
            "slug": "auto-start-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create zone
        zone_payload = {"name": "Auto Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        # Create first batch (T1-T5)
        resp1 = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 5, "starting_number": 1},
        )
        assert resp1.status_code == 201

        # Create second batch WITHOUT starting_number (should be T6-T8)
        resp2 = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 3},
        )

        assert resp2.status_code == 201
        data = resp2.json()
        assert data["tables"][0]["label"] == "T6"
        assert data["tables"][1]["label"] == "T7"
        assert data["tables"][2]["label"] == "T8"

    async def test_batch_create_fill_gaps(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Batch create with fill_gaps fills gaps in existing numbering."""
        # Create exhibition
        exhibition_payload = {
            "title": "Fill Gaps Test",
            "slug": "fill-gaps-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create zone
        zone_payload = {"name": "Gaps Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        # Create tables T1, T2, T5 (gaps at 3, 4)
        await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 2, "starting_number": 1},
        )
        await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 1, "starting_number": 5},
        )

        # Create 4 more tables with fill_gaps=true
        # Should create T3, T4, T6, T7 (fills gaps first, then continues)
        response = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 4, "fill_gaps": True},
        )

        assert response.status_code == 201
        data = response.json()
        labels = [t["label"] for t in data["tables"]]
        assert labels == ["T3", "T4", "T6", "T7"]

    async def test_batch_create_fill_gaps_more_than_gaps(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Batch create with fill_gaps continues after filling all gaps."""
        # Create exhibition
        exhibition_payload = {
            "title": "Fill Gaps More Test",
            "slug": "fill-gaps-more-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create zone
        zone_payload = {"name": "More Gaps Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        # Create tables T1, T3 (gap at 2)
        await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 1, "starting_number": 1},
        )
        await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 1, "starting_number": 3},
        )

        # Create 3 tables with fill_gaps=true
        # Should create T2 (fills gap), T4, T5 (continues)
        response = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 3, "fill_gaps": True},
        )

        assert response.status_code == 201
        data = response.json()
        labels = [t["label"] for t in data["tables"]]
        assert labels == ["T2", "T4", "T5"]


class TestZoneDelegation:
    """Tests for zone delegation to partners."""

    async def test_delegate_zone_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Organizer can delegate zone to a group."""
        # Create exhibition and zone
        exhibition_payload = {
            "title": "Delegate Test",
            "slug": "delegate-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {"name": "Delegate Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]
        assert zone_resp.json()["delegated_to_group_id"] is None

        # Delegate to a group
        response = await auth_client.post(
            f"/api/v1/zones/{zone_id}/delegate",
            json={"delegated_to_group_id": test_organizer["group_id"]},
        )

        assert response.status_code == 200
        assert response.json()["delegated_to_group_id"] == test_organizer["group_id"]

    async def test_remove_delegation(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Organizer can remove zone delegation."""
        # Create exhibition and delegated zone
        exhibition_payload = {
            "title": "Remove Delegate Test",
            "slug": "remove-delegate-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {
            "name": "Remove Delegate Zone",
            "exhibition_id": exhibition_id,
            "delegated_to_group_id": test_organizer["group_id"],
        }
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        # Remove delegation
        response = await auth_client.post(
            f"/api/v1/zones/{zone_id}/delegate",
            json={"delegated_to_group_id": None},
        )

        assert response.status_code == 200
        assert response.json()["delegated_to_group_id"] is None

    async def test_delegate_forbidden_for_user(
        self, auth_client: AsyncClient, client: AsyncClient, test_user: dict, test_organizer: dict
    ):
        """Regular user cannot delegate zones."""
        # Create exhibition and zone
        exhibition_payload = {
            "title": "User Delegate Test",
            "slug": "user-delegate-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {"name": "User Delegate Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        # Try to delegate as regular user
        response = await client.post(
            f"/api/v1/zones/{zone_id}/delegate",
            json={"delegated_to_group_id": test_organizer["group_id"]},
            headers={"X-User-ID": test_user["id"]},
        )

        assert response.status_code == 403


class TestPartnerPermissions:
    """Tests for partner permissions on delegated zones (#99)."""

    @pytest.fixture
    async def partner_setup(
        self, auth_client: AsyncClient, db_session: AsyncSession, test_organizer: dict
    ):
        """Create a partner user with access to a specific zone via UserExhibitionRole."""
        # Create partner user (global role is USER)
        partner_user = User(
            id=uuid4(),
            email="partner@example.com",
            hashed_password="hashed_password",
            full_name="Partner User",
            global_role=GlobalRole.USER,
            is_active=True,
        )
        db_session.add(partner_user)

        # Create a user group for the partner
        partner_group = UserGroup(
            id=uuid4(),
            organization_id=test_organizer["organization_id"],
            name="Partner Club",
            type=UserGroupType.ASSOCIATION,
        )
        db_session.add(partner_group)

        # Add partner to the group as admin
        membership = UserGroupMembership(
            id=uuid4(),
            user_id=partner_user.id,
            user_group_id=partner_group.id,
            group_role=GroupRole.ADMIN,
        )
        db_session.add(membership)
        await db_session.commit()

        # Create exhibition
        exhibition_payload = {
            "title": "Partner Test",
            "slug": "partner-test-" + str(uuid4())[:8],
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create zone for partner
        zone_payload = {
            "name": "Partner Zone",
            "exhibition_id": exhibition_id,
        }
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        delegated_zone_id = zone_resp.json()["id"]

        # Create non-delegated zone
        zone_payload2 = {
            "name": "Other Zone",
            "exhibition_id": exhibition_id,
        }
        zone_resp2 = await auth_client.post("/api/v1/zones/", json=zone_payload2)
        other_zone_id = zone_resp2.json()["id"]

        # Assign PARTNER role with access to the delegated zone via UserExhibitionRole
        partner_role = UserExhibitionRole(
            id=uuid4(),
            user_id=partner_user.id,
            exhibition_id=exhibition_id,
            role=ExhibitionRole.PARTNER,
            zone_ids=[delegated_zone_id],  # Only access to this zone
        )
        db_session.add(partner_role)
        await db_session.commit()

        return {
            "partner_user_id": str(partner_user.id),
            "partner_group_id": str(partner_group.id),
            "delegated_zone_id": delegated_zone_id,
            "other_zone_id": other_zone_id,
            "exhibition_id": exhibition_id,
        }

    async def test_partner_can_manage_delegated_zone(
        self, client: AsyncClient, partner_setup: dict
    ):
        """Partner can create tables in their delegated zone."""
        response = await client.post(
            f"/api/v1/zones/{partner_setup['delegated_zone_id']}/batch-tables",
            json={"prefix": "P", "count": 3},
            headers={"X-User-ID": partner_setup["partner_user_id"]},
        )

        assert response.status_code == 201
        assert response.json()["created_count"] == 3

    async def test_partner_cannot_manage_other_zone(
        self, client: AsyncClient, partner_setup: dict
    ):
        """Partner cannot create tables in non-delegated zone."""
        response = await client.post(
            f"/api/v1/zones/{partner_setup['other_zone_id']}/batch-tables",
            json={"prefix": "X", "count": 3},
            headers={"X-User-ID": partner_setup["partner_user_id"]},
        )

        assert response.status_code == 403

    async def test_partner_can_update_delegated_zone(
        self, client: AsyncClient, partner_setup: dict
    ):
        """Partner can update their delegated zone."""
        response = await client.put(
            f"/api/v1/zones/{partner_setup['delegated_zone_id']}",
            json={"name": "Updated Partner Zone"},
            headers={"X-User-ID": partner_setup["partner_user_id"]},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Partner Zone"

    async def test_partner_cannot_update_other_zone(
        self, client: AsyncClient, partner_setup: dict
    ):
        """Partner cannot update non-delegated zone."""
        response = await client.put(
            f"/api/v1/zones/{partner_setup['other_zone_id']}",
            json={"name": "Hacked Zone"},
            headers={"X-User-ID": partner_setup["partner_user_id"]},
        )

        assert response.status_code == 403


class TestDeleteZone:
    """Tests for DELETE /api/v1/zones/{zone_id}"""

    async def test_delete_zone_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Delete existing zone returns 204."""
        # Create exhibition and zone
        exhibition_payload = {
            "title": "Delete Zone Test",
            "slug": "delete-zone-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {"name": "Zone To Delete", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        # Delete
        response = await auth_client.delete(f"/api/v1/zones/{zone_id}")

        assert response.status_code == 204

        # Verify deleted
        get_resp = await auth_client.get(f"/api/v1/zones/{zone_id}")
        assert get_resp.status_code == 404

    async def test_delete_zone_not_found(self, auth_client: AsyncClient):
        """Delete non-existent zone returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await auth_client.delete(f"/api/v1/zones/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Zone not found"

    async def test_delete_zone_unauthorized(self, client: AsyncClient):
        """Delete without auth returns 401."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.delete(f"/api/v1/zones/{fake_id}")

        assert response.status_code == 401

    async def test_delete_zone_forbidden_user_role(
        self, auth_client: AsyncClient, client: AsyncClient, test_user: dict, test_organizer: dict
    ):
        """Delete with USER role returns 403."""
        # Create exhibition and zone first
        exhibition_payload = {
            "title": "Forbidden Delete Test",
            "slug": "forbidden-delete-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {"name": "Forbidden Delete Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        response = await client.delete(
            f"/api/v1/zones/{zone_id}",
            headers={"X-User-ID": test_user["id"]},
        )

        assert response.status_code == 403


class TestUpdateTable:
    """Tests for PUT /api/v1/zones/{zone_id}/tables/{table_id}"""

    async def test_update_table_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Update table returns 200 with updated data."""
        # Create exhibition, zone, and table
        exhibition_payload = {
            "title": "Update Table Test",
            "slug": "update-table-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {"name": "Update Table Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        # Create a table
        tables_resp = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 1, "capacity": 4},
        )
        table_id = tables_resp.json()["tables"][0]["id"]

        # Update the table
        response = await auth_client.put(
            f"/api/v1/zones/{zone_id}/tables/{table_id}",
            json={"label": "VIP-1", "capacity": 8, "status": "RESERVED"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "VIP-1"
        assert data["capacity"] == 8
        assert data["status"] == "RESERVED"

    async def test_update_table_not_found(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Update non-existent table returns 404."""
        # Create exhibition and zone
        exhibition_payload = {
            "title": "Update Table Not Found",
            "slug": "update-table-not-found",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {"name": "Not Found Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        fake_table_id = "00000000-0000-0000-0000-000000000000"

        response = await auth_client.put(
            f"/api/v1/zones/{zone_id}/tables/{fake_table_id}",
            json={"label": "Updated"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Physical table not found"

    async def test_update_table_unauthorized(self, client: AsyncClient):
        """Update without auth returns 401."""
        fake_zone_id = "00000000-0000-0000-0000-000000000000"
        fake_table_id = "00000000-0000-0000-0000-000000000001"

        response = await client.put(
            f"/api/v1/zones/{fake_zone_id}/tables/{fake_table_id}",
            json={"label": "Updated"},
        )

        assert response.status_code == 401


class TestDeleteTable:
    """Tests for DELETE /api/v1/zones/{zone_id}/tables/{table_id}"""

    async def test_delete_table_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Delete table returns 204."""
        # Create exhibition, zone, and table
        exhibition_payload = {
            "title": "Delete Table Test",
            "slug": "delete-table-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {"name": "Delete Table Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        # Create a table
        tables_resp = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 1},
        )
        table_id = tables_resp.json()["tables"][0]["id"]

        # Delete the table
        response = await auth_client.delete(
            f"/api/v1/zones/{zone_id}/tables/{table_id}"
        )

        assert response.status_code == 204

        # Verify deleted
        tables_resp = await auth_client.get(f"/api/v1/zones/{zone_id}/tables")
        assert len(tables_resp.json()) == 0

    async def test_delete_table_not_found(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Delete non-existent table returns 404."""
        # Create exhibition and zone
        exhibition_payload = {
            "title": "Delete Table Not Found",
            "slug": "delete-table-not-found",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        zone_payload = {"name": "Delete Not Found Zone", "exhibition_id": exhibition_id}
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        fake_table_id = "00000000-0000-0000-0000-000000000000"

        response = await auth_client.delete(
            f"/api/v1/zones/{zone_id}/tables/{fake_table_id}"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Physical table not found"

    async def test_delete_table_unauthorized(self, client: AsyncClient):
        """Delete without auth returns 401."""
        fake_zone_id = "00000000-0000-0000-0000-000000000000"
        fake_table_id = "00000000-0000-0000-0000-000000000001"

        response = await client.delete(
            f"/api/v1/zones/{fake_zone_id}/tables/{fake_table_id}"
        )

        assert response.status_code == 401
