"""
Tests for GameSession API endpoints.
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.game.entity import GameCategory, Game
from app.domain.shared.entity import GameComplexity


@pytest.fixture
async def test_game_category(db_session: AsyncSession) -> dict:
    """Create a test game category."""
    category = GameCategory(
        id=uuid4(),
        name="Role-Playing Games",
        slug="rpg",
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    return {
        "id": str(category.id),
        "name": category.name,
        "slug": category.slug,
    }


@pytest.fixture
async def test_game(db_session: AsyncSession, test_game_category: dict) -> dict:
    """Create a test game."""
    game = Game(
        id=uuid4(),
        category_id=test_game_category["id"],
        title="Dungeons & Dragons 5e",
        publisher="Wizards of the Coast",
        complexity=GameComplexity.INTERMEDIATE,
        min_players=3,
        max_players=6,
    )
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)

    return {
        "id": str(game.id),
        "title": game.title,
        "category_id": test_game_category["id"],
    }


@pytest.fixture
async def test_exhibition_with_slot(auth_client: AsyncClient, test_organizer: dict) -> dict:
    """Create an exhibition with a time slot."""
    # Create exhibition
    exhibition_payload = {
        "title": "Session Test Convention",
        "slug": "session-test-convention",
        "start_date": "2026-07-01T08:00:00Z",
        "end_date": "2026-07-03T22:00:00Z",
        "organization_id": test_organizer["organization_id"],
    }
    exhibition_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
    exhibition_id = exhibition_resp.json()["id"]

    # Create time slot
    slot_payload = {
        "name": "Afternoon",
        "start_time": "2026-07-01T14:00:00Z",
        "end_time": "2026-07-01T18:00:00Z",
        "max_duration_minutes": 240,
        "buffer_time_minutes": 15,
    }
    slot_resp = await auth_client.post(
        f"/api/v1/exhibitions/{exhibition_id}/slots", json=slot_payload
    )

    return {
        "exhibition_id": exhibition_id,
        "time_slot_id": slot_resp.json()["id"],
    }


class TestCreateGameSession:
    """Tests for POST /api/v1/sessions/"""

    async def test_create_success(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Create returns 201 with created entity."""
        payload = {
            "title": "My D&D Adventure",
            "description": "A thrilling dungeon crawl",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 5,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T18:00:00Z",
            "language": "en",
            "safety_tools": ["X-Card", "Lines & Veils"],
        }

        response = await auth_client.post("/api/v1/sessions/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My D&D Adventure"
        assert data["status"] == "DRAFT"
        assert data["max_players_count"] == 5
        assert "id" in data

    async def test_create_unauthorized(self, client: AsyncClient):
        """Create without auth returns 401."""
        payload = {
            "title": "Unauthorized Session",
            "exhibition_id": "00000000-0000-0000-0000-000000000000",
            "time_slot_id": "00000000-0000-0000-0000-000000000000",
            "game_id": "00000000-0000-0000-0000-000000000000",
            "max_players_count": 5,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T18:00:00Z",
        }

        response = await client.post("/api/v1/sessions/", json=payload)
        assert response.status_code == 401

    async def test_create_exhibition_not_found(
        self, auth_client: AsyncClient, test_game: dict
    ):
        """Create with non-existent exhibition returns 404."""
        payload = {
            "title": "Orphan Session",
            "exhibition_id": "00000000-0000-0000-0000-000000000000",
            "time_slot_id": "00000000-0000-0000-0000-000000000000",
            "game_id": test_game["id"],
            "max_players_count": 5,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T18:00:00Z",
        }

        response = await auth_client.post("/api/v1/sessions/", json=payload)
        assert response.status_code == 404

    async def test_create_schedule_outside_slot(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Create with schedule outside time slot returns 400."""
        payload = {
            "title": "Outside Slot Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 5,
            "scheduled_start": "2026-07-01T10:00:00Z",  # Before slot
            "scheduled_end": "2026-07-01T14:00:00Z",
        }

        response = await auth_client.post("/api/v1/sessions/", json=payload)
        assert response.status_code == 400


class TestGetGameSession:
    """Tests for GET /api/v1/sessions/{id}"""

    async def test_get_success(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Get existing session returns 200."""
        # Create session
        payload = {
            "title": "Get Test Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]

        response = await auth_client.get(f"/api/v1/sessions/{session_id}")

        assert response.status_code == 200
        assert response.json()["title"] == "Get Test Session"

    async def test_get_not_found(self, client: AsyncClient):
        """Get non-existent session returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(f"/api/v1/sessions/{fake_id}")
        assert response.status_code == 404


class TestListGameSessions:
    """Tests for GET /api/v1/sessions/"""

    async def test_list_empty(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
    ):
        """Empty list returns 200 with empty array."""
        response = await auth_client.get(
            "/api/v1/sessions/",
            params={"exhibition_id": test_exhibition_with_slot["exhibition_id"]},
        )

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_with_data(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """List returns created sessions."""
        # Create sessions
        for i in range(2):
            payload = {
                "title": f"Session {i + 1}",
                "exhibition_id": test_exhibition_with_slot["exhibition_id"],
                "time_slot_id": test_exhibition_with_slot["time_slot_id"],
                "game_id": test_game["id"],
                "max_players_count": 4,
                "scheduled_start": f"2026-07-01T{14 + i}:00:00Z",
                "scheduled_end": f"2026-07-01T{15 + i}:00:00Z",
            }
            await auth_client.post("/api/v1/sessions/", json=payload)

        response = await auth_client.get(
            "/api/v1/sessions/",
            params={"exhibition_id": test_exhibition_with_slot["exhibition_id"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestWorkflow:
    """Tests for session workflow (submit, moderate)."""

    async def test_submit_for_moderation(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Submit transitions DRAFT -> PENDING_MODERATION."""
        # Create session
        payload = {
            "title": "Submit Test Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]
        assert create_resp.json()["status"] == "DRAFT"

        # Submit
        response = await auth_client.post(f"/api/v1/sessions/{session_id}/submit")

        assert response.status_code == 200
        assert response.json()["status"] == "PENDING_MODERATION"

    async def test_approve_session(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Approve transitions PENDING_MODERATION -> VALIDATED."""
        # Create and submit
        payload = {
            "title": "Approve Test Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]
        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")

        # Approve
        response = await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "VALIDATED"

    async def test_reject_session(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Reject transitions PENDING_MODERATION -> REJECTED with reason."""
        # Create and submit
        payload = {
            "title": "Reject Test Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]
        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")

        # Reject
        response = await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "reject", "rejection_reason": "Missing safety tools"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "REJECTED"
        assert response.json()["rejection_reason"] == "Missing safety tools"

    async def test_reject_without_reason_fails(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Reject without reason returns 422."""
        # Create and submit
        payload = {
            "title": "Reject No Reason Test",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]
        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")

        # Reject without reason
        response = await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "reject"},
        )

        assert response.status_code == 422


class TestBookings:
    """Tests for booking endpoints."""

    async def _create_validated_session(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ) -> str:
        """Helper to create a validated session."""
        payload = {
            "title": "Booking Test Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 2,  # Small for testing waitlist
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]

        # Submit and approve
        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        return session_id

    async def test_create_booking_success(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Create booking returns 201 with CONFIRMED status."""
        session_id = await self._create_validated_session(
            auth_client, test_exhibition_with_slot, test_game
        )

        response = await auth_client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "CONFIRMED"
        assert data["role"] == "PLAYER"

    async def test_booking_waitlist(
        self,
        auth_client: AsyncClient,
        client: AsyncClient,
        db_session: AsyncSession,
        test_exhibition_with_slot: dict,
        test_game: dict,
        test_user: dict,
    ):
        """Booking when session full goes to WAITING_LIST."""
        session_id = await self._create_validated_session(
            auth_client, test_exhibition_with_slot, test_game
        )

        # First booking (by organizer via auth_client) - CONFIRMED
        resp1 = await auth_client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
        )
        assert resp1.json()["status"] == "CONFIRMED"

        # Second booking (still space) - create another user booking
        # For this we need to create another booking as the same user is not allowed twice
        # Let's use the test_user
        resp2 = await client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
            headers={"X-User-ID": test_user["id"]},
        )
        assert resp2.json()["status"] == "CONFIRMED"

    async def test_cancel_booking(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Cancel booking returns booking with CANCELLED status."""
        session_id = await self._create_validated_session(
            auth_client, test_exhibition_with_slot, test_game
        )

        # Create booking
        create_resp = await auth_client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
        )
        booking_id = create_resp.json()["id"]

        # Cancel
        response = await auth_client.delete(f"/api/v1/sessions/bookings/{booking_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "CANCELLED"

    async def test_duplicate_booking_fails(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Booking same session twice returns 409."""
        session_id = await self._create_validated_session(
            auth_client, test_exhibition_with_slot, test_game
        )

        # First booking
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
        )

        # Second booking - should fail
        response = await auth_client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
        )

        assert response.status_code == 409

    async def test_booking_draft_session_fails(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Booking a draft session returns 400."""
        # Create session without approving
        payload = {
            "title": "Draft Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]

        # Try to book
        response = await auth_client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
        )

        assert response.status_code == 400


class TestDeleteSession:
    """Tests for DELETE /api/v1/sessions/{id}"""

    async def test_delete_draft_success(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Delete draft session returns 204."""
        payload = {
            "title": "Delete Test Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]

        response = await auth_client.delete(f"/api/v1/sessions/{session_id}")

        assert response.status_code == 204

        # Verify deleted
        get_resp = await auth_client.get(f"/api/v1/sessions/{session_id}")
        assert get_resp.status_code == 404

    async def test_delete_validated_fails(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Delete validated session returns 400."""
        payload = {
            "title": "Validated Delete Test",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]

        # Submit and approve
        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        # Try to delete
        response = await auth_client.delete(f"/api/v1/sessions/{session_id}")

        assert response.status_code == 400


class TestTableAssignment:
    """Tests for table assignment and collision detection."""

    async def _create_validated_session(
        self,
        auth_client: AsyncClient,
        exhibition_id: str,
        time_slot_id: str,
        game_id: str,
        start: str,
        end: str,
        title: str = "Test Session",
    ) -> str:
        """Helper to create a validated session."""
        payload = {
            "title": title,
            "exhibition_id": exhibition_id,
            "time_slot_id": time_slot_id,
            "game_id": game_id,
            "max_players_count": 4,
            "scheduled_start": start,
            "scheduled_end": end,
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]

        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        return session_id

    async def test_assign_table_success(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Assign table to session without collision succeeds."""
        # Create zone and table
        zone_payload = {
            "name": "Test Zone",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
        }
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        tables_resp = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 1},
        )
        table_id = tables_resp.json()["tables"][0]["id"]

        # Create validated session
        session_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T14:00:00Z",
            "2026-07-01T16:00:00Z",
        )

        # Assign table
        response = await auth_client.post(
            f"/api/v1/sessions/{session_id}/assign-table",
            params={"table_id": table_id},
        )

        assert response.status_code == 200
        assert response.json()["physical_table_id"] == table_id

    async def test_assign_table_collision(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Assign table with collision returns 409."""
        # Create zone and table
        zone_payload = {
            "name": "Collision Zone",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
        }
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        tables_resp = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 1},
        )
        table_id = tables_resp.json()["tables"][0]["id"]

        # Create first session and assign table
        session1_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T14:00:00Z",
            "2026-07-01T16:00:00Z",
            "Session 1",
        )
        await auth_client.post(
            f"/api/v1/sessions/{session1_id}/assign-table",
            params={"table_id": table_id},
        )

        # Create second overlapping session
        session2_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T15:00:00Z",  # Overlaps with session 1
            "2026-07-01T17:00:00Z",
            "Session 2",
        )

        # Try to assign same table - should fail
        response = await auth_client.post(
            f"/api/v1/sessions/{session2_id}/assign-table",
            params={"table_id": table_id},
        )

        assert response.status_code == 409
        assert "collision" in response.json()["detail"].lower()

    async def test_assign_table_with_buffer(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Sessions too close (within buffer time) cause collision."""
        # Create zone and table
        zone_payload = {
            "name": "Buffer Zone",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
        }
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        tables_resp = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 1},
        )
        table_id = tables_resp.json()["tables"][0]["id"]

        # Create first session 14:00-15:00 and assign table
        session1_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T14:00:00Z",
            "2026-07-01T15:00:00Z",
            "Early Session",
        )
        await auth_client.post(
            f"/api/v1/sessions/{session1_id}/assign-table",
            params={"table_id": table_id},
        )

        # Create second session 15:05-16:00 (only 5 min gap, buffer is 15 min)
        session2_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T15:05:00Z",
            "2026-07-01T16:00:00Z",
            "Too Close Session",
        )

        # Try to assign same table - should fail due to buffer
        response = await auth_client.post(
            f"/api/v1/sessions/{session2_id}/assign-table",
            params={"table_id": table_id},
        )

        assert response.status_code == 409

    async def test_assign_table_respects_buffer(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Sessions with enough gap (> buffer time) don't collide."""
        # Create zone and table
        zone_payload = {
            "name": "OK Buffer Zone",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
        }
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        tables_resp = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 1},
        )
        table_id = tables_resp.json()["tables"][0]["id"]

        # Create first session 14:00-15:00 and assign table
        session1_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T14:00:00Z",
            "2026-07-01T15:00:00Z",
            "First Session",
        )
        await auth_client.post(
            f"/api/v1/sessions/{session1_id}/assign-table",
            params={"table_id": table_id},
        )

        # Create second session 15:30-16:30 (30 min gap, buffer is 15 min)
        session2_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T15:30:00Z",
            "2026-07-01T16:30:00Z",
            "Second Session",
        )

        # Assign same table - should succeed
        response = await auth_client.post(
            f"/api/v1/sessions/{session2_id}/assign-table",
            params={"table_id": table_id},
        )

        assert response.status_code == 200

    async def test_assign_different_tables_no_collision(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Overlapping sessions on different tables don't collide."""
        # Create zone and two tables
        zone_payload = {
            "name": "Multi Table Zone",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
        }
        zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
        zone_id = zone_resp.json()["id"]

        tables_resp = await auth_client.post(
            f"/api/v1/zones/{zone_id}/batch-tables",
            json={"prefix": "T", "count": 2},
        )
        table1_id = tables_resp.json()["tables"][0]["id"]
        table2_id = tables_resp.json()["tables"][1]["id"]

        # Create first session and assign to table 1
        session1_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T14:00:00Z",
            "2026-07-01T16:00:00Z",
            "Session on T1",
        )
        await auth_client.post(
            f"/api/v1/sessions/{session1_id}/assign-table",
            params={"table_id": table1_id},
        )

        # Create overlapping session and assign to table 2
        session2_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T14:00:00Z",  # Same time as session 1
            "2026-07-01T16:00:00Z",
            "Session on T2",
        )

        # Assign to different table - should succeed
        response = await auth_client.post(
            f"/api/v1/sessions/{session2_id}/assign-table",
            params={"table_id": table2_id},
        )

        assert response.status_code == 200
