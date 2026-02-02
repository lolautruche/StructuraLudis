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

    async def test_list_with_data(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """List returns created exhibitions."""
        # Create an exhibition first
        payload = {
            "title": "Test Convention",
            "slug": "test-convention-list",
            "start_date": "2026-06-15T09:00:00Z",
            "end_date": "2026-06-17T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=payload)
        assert create_resp.status_code == 201

        # List should contain it (note: test_organizer fixture creates one too)
        response = await auth_client.get("/api/v1/exhibitions/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        titles = [e["title"] for e in data]
        assert "Test Convention" in titles


class TestCreateExhibition:
    """Tests for POST /api/v1/exhibitions/"""

    async def test_create_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Create returns 201 with created entity."""
        payload = {
            "title": "New Exhibition",
            "slug": "new-exhibition",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
            "city": "Paris",
            "country_code": "FR",
        }

        response = await auth_client.post("/api/v1/exhibitions/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Exhibition"
        assert data["slug"] == "new-exhibition"
        assert data["city"] == "Paris"
        assert data["status"] == "DRAFT"
        assert data["timezone"] == "UTC"
        assert data["grace_period_minutes"] == 15
        assert "id" in data
        assert "created_at" in data

    async def test_create_unauthorized(
        self, client: AsyncClient, test_organization: dict
    ):
        """Create without auth returns 401."""
        payload = {
            "title": "Unauthorized Exhibition",
            "slug": "unauth-exhibition",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organization["id"],
        }

        response = await client.post("/api/v1/exhibitions/", json=payload)
        assert response.status_code == 401

    async def test_create_forbidden_user_role(
        self, client: AsyncClient, test_user: dict, test_organization: dict
    ):
        """Create with USER role returns 403."""
        payload = {
            "title": "Forbidden Exhibition",
            "slug": "forbidden-exhibition",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organization["id"],
        }

        response = await client.post(
            "/api/v1/exhibitions/",
            json=payload,
            headers={"X-User-ID": test_user["id"]},
        )
        assert response.status_code == 403

    async def test_create_duplicate_slug(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Duplicate slug returns 409 Conflict."""
        payload = {
            "title": "Exhibition 1",
            "slug": "same-slug",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }

        # Create first one
        response1 = await auth_client.post("/api/v1/exhibitions/", json=payload)
        assert response1.status_code == 201

        # Try to create duplicate
        payload["title"] = "Exhibition 2"
        response2 = await auth_client.post("/api/v1/exhibitions/", json=payload)

        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    async def test_create_invalid_dates(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """End date before start date returns 422."""
        payload = {
            "title": "Invalid Dates",
            "slug": "invalid-dates",
            "start_date": "2026-07-05T10:00:00Z",
            "end_date": "2026-07-01T18:00:00Z",  # Before start
            "organization_id": test_organizer["organization_id"],
        }

        response = await auth_client.post("/api/v1/exhibitions/", json=payload)
        assert response.status_code == 422

    async def test_create_validation_error(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Missing required field returns 422."""
        payload = {
            "slug": "missing-title",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }

        response = await auth_client.post("/api/v1/exhibitions/", json=payload)
        assert response.status_code == 422


class TestGetExhibition:
    """Tests for GET /api/v1/exhibitions/{id}"""

    async def test_get_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Get existing exhibition returns 200."""
        # Create first
        payload = {
            "title": "Get Test",
            "slug": "get-test",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_response = await auth_client.post("/api/v1/exhibitions/", json=payload)
        exhibition_id = create_response.json()["id"]

        # Get it (no auth required for read)
        response = await auth_client.get(f"/api/v1/exhibitions/{exhibition_id}")

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

    async def test_update_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Update returns 200 with updated entity."""
        # Create first
        payload = {
            "title": "Before Update",
            "slug": "update-test",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_response = await auth_client.post("/api/v1/exhibitions/", json=payload)
        exhibition_id = create_response.json()["id"]

        # Update it
        update_payload = {
            "title": "After Update",
            "description": "Updated description",
            "status": "PUBLISHED",
        }
        response = await auth_client.put(
            f"/api/v1/exhibitions/{exhibition_id}", json=update_payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "After Update"
        assert data["description"] == "Updated description"
        assert data["status"] == "PUBLISHED"
        assert data["slug"] == "update-test"  # Unchanged
        assert data["updated_at"] is not None

    async def test_update_not_found(self, auth_client: AsyncClient):
        """Update non-existent exhibition returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await auth_client.put(
            f"/api/v1/exhibitions/{fake_id}",
            json={"title": "Whatever"},
        )

        assert response.status_code == 404


class TestDeleteExhibition:
    """Tests for DELETE /api/v1/exhibitions/{id}"""

    async def test_delete_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Delete returns 204 No Content."""
        # Create first
        payload = {
            "title": "To Delete",
            "slug": "delete-test",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_response = await auth_client.post("/api/v1/exhibitions/", json=payload)
        exhibition_id = create_response.json()["id"]

        # Delete it
        response = await auth_client.delete(f"/api/v1/exhibitions/{exhibition_id}")

        assert response.status_code == 204

        # Verify it's gone
        get_response = await auth_client.get(f"/api/v1/exhibitions/{exhibition_id}")
        assert get_response.status_code == 404

    async def test_delete_not_found(self, auth_client: AsyncClient):
        """Delete non-existent exhibition returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await auth_client.delete(f"/api/v1/exhibitions/{fake_id}")

        assert response.status_code == 404


class TestTimeSlots:
    """Tests for TimeSlot endpoints."""

    async def test_create_slot_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Create time slot returns 201."""
        # Create exhibition first
        exhibition_payload = {
            "title": "Slot Test Exhibition",
            "slug": "slot-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create time slot
        slot_payload = {
            "name": "Morning",
            "start_time": "2026-07-01T09:00:00Z",
            "end_time": "2026-07-01T13:00:00Z",
            "max_duration_minutes": 240,
            "buffer_time_minutes": 15,
        }
        response = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/slots", json=slot_payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Morning"
        assert data["max_duration_minutes"] == 240

    async def test_create_slot_outside_exhibition(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Slot outside exhibition dates returns 400."""
        # Create exhibition first
        exhibition_payload = {
            "title": "Slot Validation Test",
            "slug": "slot-validation",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-01T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Try to create slot outside exhibition dates
        slot_payload = {
            "name": "Outside",
            "start_time": "2026-07-02T09:00:00Z",  # After exhibition ends
            "end_time": "2026-07-02T13:00:00Z",
            "max_duration_minutes": 240,
        }
        response = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/slots", json=slot_payload
        )

        assert response.status_code == 400

    async def test_list_slots(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """List slots returns 200."""
        # Create exhibition
        exhibition_payload = {
            "title": "List Slots Test",
            "slug": "list-slots-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create some slots
        for i, name in enumerate(["Morning", "Afternoon", "Evening"]):
            slot_payload = {
                "name": name,
                "start_time": f"2026-07-01T{9 + i * 4:02d}:00:00Z",
                "end_time": f"2026-07-01T{13 + i * 4:02d}:00:00Z",
                "max_duration_minutes": 240,
            }
            await auth_client.post(
                f"/api/v1/exhibitions/{exhibition_id}/slots", json=slot_payload
            )

        # List them
        response = await auth_client.get(f"/api/v1/exhibitions/{exhibition_id}/slots")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    async def test_update_slot_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Update time slot returns 200 with updated data."""
        # Create exhibition
        exhibition_payload = {
            "title": "Update Slot Test",
            "slug": "update-slot-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create a slot
        slot_payload = {
            "name": "Morning",
            "start_time": "2026-07-01T09:00:00Z",
            "end_time": "2026-07-01T13:00:00Z",
            "max_duration_minutes": 240,
            "buffer_time_minutes": 15,
        }
        slot_resp = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/slots", json=slot_payload
        )
        slot_id = slot_resp.json()["id"]

        # Update the slot
        update_payload = {
            "name": "Early Morning",
            "buffer_time_minutes": 30,
        }
        response = await auth_client.put(
            f"/api/v1/exhibitions/{exhibition_id}/slots/{slot_id}",
            json=update_payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Early Morning"
        assert data["buffer_time_minutes"] == 30
        assert data["max_duration_minutes"] == 240  # Unchanged

    async def test_update_slot_not_found(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Update non-existent slot returns 404."""
        # Create exhibition
        exhibition_payload = {
            "title": "Update Slot 404 Test",
            "slug": "update-slot-404",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        fake_slot_id = "00000000-0000-0000-0000-000000000000"
        response = await auth_client.put(
            f"/api/v1/exhibitions/{exhibition_id}/slots/{fake_slot_id}",
            json={"name": "Whatever"},
        )

        assert response.status_code == 404

    async def test_delete_slot_success(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Delete time slot returns 204."""
        # Create exhibition
        exhibition_payload = {
            "title": "Delete Slot Test",
            "slug": "delete-slot-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create a slot
        slot_payload = {
            "name": "To Delete",
            "start_time": "2026-07-01T09:00:00Z",
            "end_time": "2026-07-01T13:00:00Z",
            "max_duration_minutes": 240,
        }
        slot_resp = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/slots", json=slot_payload
        )
        slot_id = slot_resp.json()["id"]

        # Delete the slot
        response = await auth_client.delete(
            f"/api/v1/exhibitions/{exhibition_id}/slots/{slot_id}"
        )
        assert response.status_code == 204

        # Verify it's gone
        list_resp = await auth_client.get(f"/api/v1/exhibitions/{exhibition_id}/slots")
        assert len(list_resp.json()) == 0

    async def test_delete_slot_not_found(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Delete non-existent slot returns 404."""
        # Create exhibition
        exhibition_payload = {
            "title": "Delete Slot 404 Test",
            "slug": "delete-slot-404",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        fake_slot_id = "00000000-0000-0000-0000-000000000000"
        response = await auth_client.delete(
            f"/api/v1/exhibitions/{exhibition_id}/slots/{fake_slot_id}"
        )

        assert response.status_code == 404


class TestDashboard:
    """Tests for GET /api/v1/exhibitions/{id}/status (dashboard)."""

    async def test_dashboard_empty_exhibition(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Dashboard for exhibition with no zones/tables returns zeros."""
        # Create exhibition
        exhibition_payload = {
            "title": "Empty Dashboard Test",
            "slug": "empty-dashboard",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Get dashboard
        response = await auth_client.get(f"/api/v1/exhibitions/{exhibition_id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["exhibition_id"] == exhibition_id
        assert data["total_zones"] == 0
        assert data["total_tables"] == 0
        assert data["tables_available"] == 0
        assert data["tables_occupied"] == 0
        assert data["occupation_rate"] == 0.0
        assert data["sessions_by_status"] == []
        assert data["total_sessions"] == 0
        assert data["total_bookings"] == 0

    async def test_dashboard_with_zones_and_tables(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Dashboard shows correct counts for zones and tables."""
        # Create exhibition
        exhibition_payload = {
            "title": "Dashboard with Data",
            "slug": "dashboard-data",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create zones via API
        zone_payload = {
            "name": "Main Hall",
            "exhibition_id": exhibition_id,
            "type": "MIXED",
        }
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        assert zone_resp.status_code == 201
        zone_id = zone_resp.json()["id"]

        # Create tables via batch endpoint
        tables_payload = {
            "prefix": "Table ",
            "count": 10,
            "starting_number": 1,
            "capacity": 6,
        }
        tables_resp = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables", json=tables_payload
        )
        assert tables_resp.status_code == 201
        assert tables_resp.json()["created_count"] == 10

        # Get dashboard
        response = await auth_client.get(f"/api/v1/exhibitions/{exhibition_id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["total_zones"] == 1
        assert data["total_tables"] == 10
        assert data["tables_available"] == 10
        assert data["tables_occupied"] == 0
        assert data["occupation_rate"] == 0.0

    async def test_dashboard_not_found(self, auth_client: AsyncClient):
        """Dashboard for non-existent exhibition returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await auth_client.get(f"/api/v1/exhibitions/{fake_id}/status")

        assert response.status_code == 404

    async def test_dashboard_unauthorized(
        self, client: AsyncClient, test_organization: dict
    ):
        """Dashboard without auth returns 401."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(f"/api/v1/exhibitions/{fake_id}/status")

        assert response.status_code == 401


class TestSafetyTools:
    """Tests for Safety Tools endpoints (JS.A5)."""

    async def _create_exhibition(
        self,
        auth_client: AsyncClient,
        organization_id: str,
        slug: str = "safety-test-exhibition",
    ) -> str:
        """Helper to create an exhibition."""
        payload = {
            "title": "Safety Test Exhibition",
            "slug": slug,
            "start_date": "2026-06-15T09:00:00Z",
            "end_date": "2026-06-17T18:00:00Z",
            "organization_id": organization_id,
        }
        resp = await auth_client.post("/api/v1/exhibitions/", json=payload)
        return resp.json()["id"]

    async def test_create_safety_tool(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Create safety tool returns 201."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "safety-create"
        )

        payload = {
            "name": "X-Card",
            "slug": "x-card",
            "description": "Tap to skip content",
            "exhibition_id": exhibition_id,
        }
        response = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools",
            json=payload,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "X-Card"
        assert data["slug"] == "x-card"
        assert data["is_required"] is False

    async def test_create_safety_tool_duplicate_slug(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Create safety tool with duplicate slug returns 409."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "safety-dup"
        )

        payload = {
            "name": "X-Card",
            "slug": "x-card",
            "exhibition_id": exhibition_id,
        }
        await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools",
            json=payload,
        )

        # Try to create again with same slug
        response = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools",
            json=payload,
        )

        assert response.status_code == 409

    async def test_list_safety_tools(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """List safety tools returns all tools ordered."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "safety-list"
        )

        # Create two tools
        await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools",
            json={"name": "Tool B", "slug": "tool-b", "display_order": 2, "exhibition_id": exhibition_id},
        )
        await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools",
            json={"name": "Tool A", "slug": "tool-a", "display_order": 1, "exhibition_id": exhibition_id},
        )

        response = await auth_client.get(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Should be ordered by display_order
        assert data[0]["name"] == "Tool A"
        assert data[1]["name"] == "Tool B"

    async def test_create_default_safety_tools(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Create default safety tools adds common tools."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "safety-defaults"
        )

        response = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools/defaults"
        )

        assert response.status_code == 201
        data = response.json()
        assert data["created_count"] >= 5  # At least 5 default tools
        assert len(data["tools"]) >= 5

        # Check some known tools exist
        slugs = [t["slug"] for t in data["tools"]]
        assert "x-card" in slugs
        assert "lines-and-veils" in slugs

    async def test_create_default_safety_tools_idempotent(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Creating defaults twice doesn't duplicate tools."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "safety-idem"
        )

        # Create defaults twice
        resp1 = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools/defaults"
        )
        resp2 = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools/defaults"
        )

        assert resp1.status_code == 201
        assert resp2.status_code == 201
        assert resp2.json()["created_count"] == 0  # No new tools created

    async def test_update_safety_tool(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Update safety tool modifies fields."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "safety-update"
        )

        # Create a tool
        create_resp = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools",
            json={"name": "Old Name", "slug": "test-tool", "exhibition_id": exhibition_id},
        )
        tool_id = create_resp.json()["id"]

        # Update it
        response = await auth_client.put(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools/{tool_id}",
            json={"name": "New Name", "is_required": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["is_required"] is True
        assert data["slug"] == "test-tool"  # Unchanged

    async def test_delete_safety_tool(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Delete safety tool removes it."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "safety-delete"
        )

        # Create a tool
        create_resp = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools",
            json={"name": "To Delete", "slug": "delete-me", "exhibition_id": exhibition_id},
        )
        tool_id = create_resp.json()["id"]

        # Delete it
        response = await auth_client.delete(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools/{tool_id}"
        )
        assert response.status_code == 204

        # Verify it's gone
        get_resp = await auth_client.get(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools/{tool_id}"
        )
        assert get_resp.status_code == 404

    async def test_list_safety_tools_public(
        self, client: AsyncClient, auth_client: AsyncClient, test_organizer: dict
    ):
        """List safety tools is public (no auth required)."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "safety-public"
        )

        # Create a tool as organizer
        await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools",
            json={"name": "Public Tool", "slug": "public", "exhibition_id": exhibition_id},
        )

        # List as unauthenticated user
        response = await client.get(
            f"/api/v1/exhibitions/{exhibition_id}/safety-tools"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1


class TestEventConfiguration:
    """Tests for event configuration fields (#39 - JS.03)."""

    async def test_create_with_registration_config(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Create exhibition with registration configuration."""
        payload = {
            "title": "Configured Event",
            "slug": "configured-event",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
            "is_registration_open": True,
            "registration_opens_at": "2026-06-01T00:00:00Z",
            "registration_closes_at": "2026-06-30T23:59:59Z",
        }

        response = await auth_client.post("/api/v1/exhibitions/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["is_registration_open"] is True
        assert data["registration_opens_at"] == "2026-06-01T00:00:00Z"
        assert data["registration_closes_at"] == "2026-06-30T23:59:59Z"

    async def test_create_with_language_config(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Create exhibition with language configuration."""
        payload = {
            "title": "Multilingual Event",
            "slug": "multilingual-event",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
            "primary_language": "fr",
            "secondary_languages": ["en", "de"],
        }

        response = await auth_client.post("/api/v1/exhibitions/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["primary_language"] == "fr"
        assert data["secondary_languages"] == ["en", "de"]

    async def test_create_defaults(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Exhibition without config uses defaults."""
        payload = {
            "title": "Default Config Event",
            "slug": "default-config-event",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }

        response = await auth_client.post("/api/v1/exhibitions/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["is_registration_open"] is False
        assert data["registration_opens_at"] is None
        assert data["registration_closes_at"] is None
        assert data["primary_language"] == "en"
        assert data["secondary_languages"] is None

    async def test_update_registration_config(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Update registration configuration."""
        # Create exhibition
        payload = {
            "title": "Update Config Test",
            "slug": "update-config-test",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=payload)
        exhibition_id = create_resp.json()["id"]

        # Update registration config
        update_payload = {
            "is_registration_open": True,
            "registration_opens_at": "2026-06-15T00:00:00Z",
            "registration_closes_at": "2026-06-28T23:59:59Z",
        }
        response = await auth_client.put(
            f"/api/v1/exhibitions/{exhibition_id}", json=update_payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_registration_open"] is True
        assert data["registration_opens_at"] == "2026-06-15T00:00:00Z"
        assert data["registration_closes_at"] == "2026-06-28T23:59:59Z"

    async def test_update_language_config(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Update language configuration."""
        # Create exhibition
        payload = {
            "title": "Language Update Test",
            "slug": "language-update-test",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
            "primary_language": "en",
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=payload)
        exhibition_id = create_resp.json()["id"]

        # Update language config
        update_payload = {
            "primary_language": "fr",
            "secondary_languages": ["en", "es"],
        }
        response = await auth_client.put(
            f"/api/v1/exhibitions/{exhibition_id}", json=update_payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["primary_language"] == "fr"
        assert data["secondary_languages"] == ["en", "es"]

    async def test_invalid_registration_dates(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Registration closes before opens returns 422."""
        payload = {
            "title": "Invalid Reg Dates",
            "slug": "invalid-reg-dates",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
            "registration_opens_at": "2026-06-30T00:00:00Z",
            "registration_closes_at": "2026-06-01T00:00:00Z",  # Before opens
        }

        response = await auth_client.post("/api/v1/exhibitions/", json=payload)
        assert response.status_code == 422


class TestCanManagePermission:
    """Tests for can_manage field in exhibition responses."""

    async def test_organizer_can_manage_own_exhibition(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Organizer sees can_manage=true for their own exhibition."""
        # Create exhibition
        payload = {
            "title": "My Exhibition",
            "slug": "my-exhibition",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=payload)
        assert create_resp.status_code == 201
        exhibition_id = create_resp.json()["id"]

        # Get exhibition with auth
        response = await auth_client.get(f"/api/v1/exhibitions/{exhibition_id}")

        assert response.status_code == 200
        assert response.json()["can_manage"] is True

    async def test_anonymous_cannot_manage(
        self, client: AsyncClient, auth_client: AsyncClient, test_organizer: dict
    ):
        """Anonymous user sees can_manage=false."""
        # Create exhibition (with auth)
        payload = {
            "title": "Public Exhibition",
            "slug": "public-exhibition",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=payload)
        exhibition_id = create_resp.json()["id"]

        # Get without auth
        response = await client.get(f"/api/v1/exhibitions/{exhibition_id}")

        assert response.status_code == 200
        assert response.json()["can_manage"] is False

    async def test_regular_user_cannot_manage(
        self, client: AsyncClient, auth_client: AsyncClient,
        test_organizer: dict, test_user: dict
    ):
        """Regular user sees can_manage=false."""
        # Create exhibition (with organizer auth)
        payload = {
            "title": "Organizer Exhibition",
            "slug": "organizer-exhibition",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=payload)
        exhibition_id = create_resp.json()["id"]

        # Get with regular user auth
        response = await client.get(
            f"/api/v1/exhibitions/{exhibition_id}",
            headers={"X-User-ID": test_user["id"]},
        )

        assert response.status_code == 200
        assert response.json()["can_manage"] is False

    async def test_super_admin_can_manage_all(
        self, client: AsyncClient, auth_client: AsyncClient,
        test_organizer: dict, test_super_admin: dict
    ):
        """Super admin sees can_manage=true for all exhibitions."""
        # Create exhibition (with organizer auth)
        payload = {
            "title": "Any Exhibition",
            "slug": "any-exhibition",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=payload)
        exhibition_id = create_resp.json()["id"]

        # Get with super admin auth
        response = await client.get(
            f"/api/v1/exhibitions/{exhibition_id}",
            headers={"X-User-ID": test_super_admin["id"]},
        )

        assert response.status_code == 200
        assert response.json()["can_manage"] is True

    async def test_list_exhibitions_with_can_manage(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """List exhibitions includes can_manage for each."""
        # Create exhibition
        payload = {
            "title": "List Test",
            "slug": "list-test-manage",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        await auth_client.post("/api/v1/exhibitions/", json=payload)

        # List with auth
        response = await auth_client.get("/api/v1/exhibitions/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        # Organizer should be able to manage their own exhibition
        assert any(e["can_manage"] is True for e in data)

    async def test_partner_can_see_exhibition_in_list(
        self, client: AsyncClient, auth_client: AsyncClient,
        test_organizer: dict, test_user: dict, db_session
    ):
        """Partner sees can_manage=true for exhibitions they have a PARTNER role on."""
        from uuid import uuid4
        from app.domain.user.entity import UserExhibitionRole
        from app.domain.shared.entity import ExhibitionRole

        # Create exhibition (with organizer auth)
        payload = {
            "title": "Partner Test Exhibition",
            "slug": "partner-test-exhibition",
            "start_date": "2026-07-01T10:00:00Z",
            "end_date": "2026-07-03T18:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=payload)
        exhibition_id = create_resp.json()["id"]

        # Create a zone for the partner
        zone_resp = await auth_client.post(
            f"/api/v1/zones/",
            json={
                "exhibition_id": exhibition_id,
                "name": "Partner Zone",
                "type": "RPG",
            },
        )
        zone_id = zone_resp.json()["id"]

        # Assign PARTNER role to test_user via database
        partner_role = UserExhibitionRole(
            id=uuid4(),
            user_id=test_user["id"],
            exhibition_id=exhibition_id,
            role=ExhibitionRole.PARTNER,
            zone_ids=[str(zone_id)],
        )
        db_session.add(partner_role)
        await db_session.commit()

        # Get exhibition list with partner auth
        response = await client.get(
            "/api/v1/exhibitions/",
            headers={"X-User-ID": test_user["id"]},
        )

        assert response.status_code == 200
        data = response.json()
        # Partner should see the exhibition with can_manage=True
        partner_exhibitions = [e for e in data if e["id"] == exhibition_id]
        assert len(partner_exhibitions) == 1
        assert partner_exhibitions[0]["can_manage"] is True

    async def test_organizer_cannot_manage_other_org_exhibition(
        self, client: AsyncClient, db_session, test_organizer: dict
    ):
        """Organizer sees can_manage=false for another organization's exhibition."""
        from uuid import uuid4
        from app.domain.organization import Organization
        from app.domain.exhibition import Exhibition
        from app.domain.shared.entity import ExhibitionStatus
        from datetime import datetime, timezone

        # Create another organization
        other_org = Organization(
            id=uuid4(),
            name="Other Convention",
            slug="other-convention",
            contact_email="other@example.com",
        )
        db_session.add(other_org)
        await db_session.commit()

        # Create exhibition for other org
        other_exhibition = Exhibition(
            id=uuid4(),
            organization_id=other_org.id,
            title="Other Org Exhibition",
            slug="other-org-exhibition",
            start_date=datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc),
            end_date=datetime(2026, 7, 3, 18, 0, 0, tzinfo=timezone.utc),
            status=ExhibitionStatus.DRAFT,
        )
        db_session.add(other_exhibition)
        await db_session.commit()

        # Get with organizer auth (not member of other org)
        response = await client.get(
            f"/api/v1/exhibitions/{other_exhibition.id}",
            headers={"X-User-ID": test_organizer["id"]},
        )

        assert response.status_code == 200
        assert response.json()["can_manage"] is False


class TestExhibitionRoleManagement:
    """Tests for Exhibition Role Management endpoints (#99)."""

    async def _create_exhibition(
        self,
        auth_client: AsyncClient,
        organization_id: str,
        slug: str = "role-test-exhibition",
    ) -> str:
        """Helper to create an exhibition."""
        payload = {
            "title": "Role Test Exhibition",
            "slug": slug,
            "start_date": "2026-06-15T09:00:00Z",
            "end_date": "2026-06-17T18:00:00Z",
            "organization_id": organization_id,
        }
        resp = await auth_client.post("/api/v1/exhibitions/", json=payload)
        assert resp.status_code == 201
        return resp.json()["id"]

    async def _create_zone(
        self,
        auth_client: AsyncClient,
        exhibition_id: str,
        name: str = "Test Zone",
    ) -> str:
        """Helper to create a zone."""
        payload = {
            "name": name,
            "exhibition_id": exhibition_id,
            "type": "MIXED",
        }
        resp = await auth_client.post("/api/v1/zones/", json=payload)
        assert resp.status_code == 201
        return resp.json()["id"]

    async def test_list_roles_empty(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """List roles for new exhibition shows only creator as ORGANIZER."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "list-roles-empty"
        )

        response = await auth_client.get(f"/api/v1/exhibitions/{exhibition_id}/roles")

        assert response.status_code == 200
        data = response.json()
        # Creator is automatically assigned as ORGANIZER
        assert len(data) == 1
        assert data[0]["role"] == "ORGANIZER"
        assert data[0]["user_id"] == test_organizer["user_id"]

    async def test_assign_organizer_role(
        self, auth_client: AsyncClient, test_organizer: dict, test_user: dict
    ):
        """Assign ORGANIZER role to another user."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "assign-organizer"
        )

        response = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/roles",
            json={"user_id": test_user["id"], "role": "ORGANIZER"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == test_user["id"]
        assert data["role"] == "ORGANIZER"
        assert data["user_email"] is not None
        assert data["zone_ids"] is None

    async def test_assign_partner_role_with_zones(
        self, auth_client: AsyncClient, test_organizer: dict, test_user: dict
    ):
        """Assign PARTNER role with zone_ids."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "assign-partner"
        )
        zone_id = await self._create_zone(auth_client, exhibition_id, "Partner Zone")

        response = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/roles",
            json={
                "user_id": test_user["id"],
                "role": "PARTNER",
                "zone_ids": [zone_id],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "PARTNER"
        assert zone_id in data["zone_ids"]

    async def test_assign_partner_without_zones_fails(
        self, auth_client: AsyncClient, test_organizer: dict, test_user: dict
    ):
        """PARTNER role without zone_ids returns 422."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "partner-no-zones"
        )

        response = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/roles",
            json={"user_id": test_user["id"], "role": "PARTNER"},
        )

        assert response.status_code == 422

    async def test_assign_duplicate_role_fails(
        self, auth_client: AsyncClient, test_organizer: dict, test_user: dict
    ):
        """Cannot assign role to user who already has one for this exhibition."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "dup-role"
        )

        # Assign first role
        await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/roles",
            json={"user_id": test_user["id"], "role": "ORGANIZER"},
        )

        # Try to assign again
        response = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/roles",
            json={"user_id": test_user["id"], "role": "ORGANIZER"},
        )

        assert response.status_code == 409

    async def test_assign_role_invalid_zone_fails(
        self, auth_client: AsyncClient, test_organizer: dict, test_user: dict
    ):
        """Cannot assign PARTNER with zone_ids from another exhibition."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "invalid-zone"
        )
        # Create another exhibition with a zone
        other_exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "other-exhibition"
        )
        other_zone_id = await self._create_zone(
            auth_client, other_exhibition_id, "Other Zone"
        )

        response = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/roles",
            json={
                "user_id": test_user["id"],
                "role": "PARTNER",
                "zone_ids": [other_zone_id],
            },
        )

        assert response.status_code == 400
        assert "Invalid zone IDs" in response.json()["detail"]

    async def test_update_role(
        self, auth_client: AsyncClient, test_organizer: dict, test_user: dict
    ):
        """Update a role assignment."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "update-role"
        )
        zone_id = await self._create_zone(auth_client, exhibition_id, "Zone 1")

        # Assign as ORGANIZER
        create_resp = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/roles",
            json={"user_id": test_user["id"], "role": "ORGANIZER"},
        )
        role_id = create_resp.json()["id"]

        # Update to PARTNER with zones
        response = await auth_client.patch(
            f"/api/v1/exhibitions/{exhibition_id}/roles/{role_id}",
            json={"role": "PARTNER", "zone_ids": [zone_id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "PARTNER"
        assert zone_id in data["zone_ids"]

    async def test_update_partner_zones(
        self, auth_client: AsyncClient, test_organizer: dict, test_user: dict
    ):
        """Update PARTNER zone assignments."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "update-zones"
        )
        zone1_id = await self._create_zone(auth_client, exhibition_id, "Zone 1")
        zone2_id = await self._create_zone(auth_client, exhibition_id, "Zone 2")

        # Assign as PARTNER with zone1
        create_resp = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/roles",
            json={
                "user_id": test_user["id"],
                "role": "PARTNER",
                "zone_ids": [zone1_id],
            },
        )
        role_id = create_resp.json()["id"]

        # Update to include zone2
        response = await auth_client.patch(
            f"/api/v1/exhibitions/{exhibition_id}/roles/{role_id}",
            json={"zone_ids": [zone1_id, zone2_id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["zone_ids"]) == 2
        assert zone1_id in data["zone_ids"]
        assert zone2_id in data["zone_ids"]

    async def test_delete_role(
        self, auth_client: AsyncClient, test_organizer: dict, test_user: dict
    ):
        """Delete a role assignment."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "delete-role"
        )

        # Assign role
        create_resp = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/roles",
            json={"user_id": test_user["id"], "role": "ORGANIZER"},
        )
        role_id = create_resp.json()["id"]

        # Delete it
        response = await auth_client.delete(
            f"/api/v1/exhibitions/{exhibition_id}/roles/{role_id}"
        )

        assert response.status_code == 204

        # Verify it's gone
        list_resp = await auth_client.get(
            f"/api/v1/exhibitions/{exhibition_id}/roles"
        )
        role_ids = [r["id"] for r in list_resp.json()]
        assert role_id not in role_ids

    async def test_cannot_remove_yourself(
        self, auth_client: AsyncClient, test_organizer: dict
    ):
        """Cannot remove yourself from an exhibition (Issue #99)."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "self-remove"
        )

        # Get the creator's role (which is the current user)
        list_resp = await auth_client.get(
            f"/api/v1/exhibitions/{exhibition_id}/roles"
        )
        role_id = list_resp.json()[0]["id"]

        # Try to delete your own role
        response = await auth_client.delete(
            f"/api/v1/exhibitions/{exhibition_id}/roles/{role_id}"
        )

        assert response.status_code == 400
        assert "Cannot remove yourself" in response.json()["detail"]

    async def test_is_main_organizer_flag(
        self, auth_client: AsyncClient, second_auth_client: AsyncClient,
        test_organizer: dict, db_session
    ):
        """The is_main_organizer flag correctly identifies the exhibition creator (Issue #99)."""
        from app.domain.user.entity import UserExhibitionRole
        from app.domain.shared.entity import ExhibitionRole
        from uuid import uuid4

        # Create exhibition as test_organizer (becomes main organizer)
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "main-org-flag"
        )

        # Get second_organizer user ID
        second_resp = await second_auth_client.get("/api/v1/users/me")
        second_user_id = second_resp.json()["id"]

        # Grant ORGANIZER role to second_organizer
        second_role = UserExhibitionRole(
            id=uuid4(),
            user_id=second_user_id,
            exhibition_id=exhibition_id,
            role=ExhibitionRole.ORGANIZER,
        )
        db_session.add(second_role)
        await db_session.commit()

        # List roles
        list_resp = await auth_client.get(
            f"/api/v1/exhibitions/{exhibition_id}/roles"
        )
        roles = list_resp.json()

        # Find main and secondary organizer
        main_org = next(r for r in roles if r["user_id"] == test_organizer["id"])
        secondary_org = next(r for r in roles if r["user_id"] == second_user_id)

        # Main organizer should have is_main_organizer=True
        assert main_org["is_main_organizer"] is True
        # Secondary organizer should have is_main_organizer=False
        assert secondary_org["is_main_organizer"] is False

    async def test_secondary_organizer_cannot_remove_main_organizer(
        self, auth_client: AsyncClient, second_auth_client: AsyncClient,
        test_organizer: dict, db_session
    ):
        """Secondary organizer cannot remove the main organizer (creator) (Issue #99)."""
        from app.domain.user.entity import UserExhibitionRole
        from app.domain.shared.entity import ExhibitionRole
        from uuid import uuid4

        # Create exhibition as test_organizer (becomes main organizer)
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "secondary-remove"
        )

        # Get second_organizer user ID
        second_resp = await second_auth_client.get("/api/v1/users/me")
        second_user_id = second_resp.json()["id"]

        # Grant ORGANIZER role to second_organizer via database
        # (we can't use API since second_organizer doesn't have a role yet)
        second_role = UserExhibitionRole(
            id=uuid4(),
            user_id=second_user_id,
            exhibition_id=exhibition_id,
            role=ExhibitionRole.ORGANIZER,
        )
        db_session.add(second_role)
        await db_session.commit()

        # Get the main organizer's role ID
        list_resp = await auth_client.get(
            f"/api/v1/exhibitions/{exhibition_id}/roles"
        )
        roles = list_resp.json()
        main_organizer_role = next(
            r for r in roles
            if r["user_id"] == test_organizer["id"]
        )

        # Secondary organizer tries to remove main organizer
        response = await second_auth_client.delete(
            f"/api/v1/exhibitions/{exhibition_id}/roles/{main_organizer_role['id']}"
        )

        assert response.status_code == 403
        assert "main organizer" in response.json()["detail"].lower()

    async def test_roles_unauthorized(
        self, client: AsyncClient, test_organizer: dict, auth_client: AsyncClient
    ):
        """Role endpoints require authentication."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "unauth-roles"
        )

        # List without auth
        response = await client.get(f"/api/v1/exhibitions/{exhibition_id}/roles")
        assert response.status_code == 401

    async def test_roles_forbidden_for_regular_user(
        self, client: AsyncClient, auth_client: AsyncClient,
        test_organizer: dict, test_user: dict
    ):
        """Regular user cannot manage roles."""
        exhibition_id = await self._create_exhibition(
            auth_client, test_organizer["organization_id"], "forbidden-roles"
        )

        # Try to list as regular user
        response = await client.get(
            f"/api/v1/exhibitions/{exhibition_id}/roles",
            headers={"X-User-ID": test_user["id"]},
        )

        assert response.status_code == 403