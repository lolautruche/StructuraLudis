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
        second_auth_client: AsyncClient,
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

        # Create second overlapping session by different GM
        session2_id = await self._create_validated_session(
            second_auth_client,
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
        second_auth_client: AsyncClient,
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

        # Create overlapping session by different GM and assign to table 2
        session2_id = await self._create_validated_session(
            second_auth_client,
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


class TestDoubleBookingPrevention:
    """Tests for preventing double-booking on overlapping sessions."""

    async def _create_validated_session(
        self,
        auth_client: AsyncClient,
        exhibition_id: str,
        time_slot_id: str,
        game_id: str,
        start: str,
        end: str,
        title: str = "Test Session",
        max_players: int = 4,
    ) -> str:
        """Helper to create a validated session."""
        payload = {
            "title": title,
            "exhibition_id": exhibition_id,
            "time_slot_id": time_slot_id,
            "game_id": game_id,
            "max_players_count": max_players,
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

    async def test_overlapping_booking_rejected(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Booking overlapping sessions returns 409."""
        # Create two overlapping sessions by different GMs
        session1_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T14:00:00Z",
            "2026-07-01T16:00:00Z",
            "Session 1",
        )
        session2_id = await self._create_validated_session(
            second_auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T15:00:00Z",  # Overlaps with session 1
            "2026-07-01T17:00:00Z",
            "Session 2",
        )

        # Book first session
        resp1 = await auth_client.post(
            f"/api/v1/sessions/{session1_id}/bookings",
            json={"role": "PLAYER"},
        )
        assert resp1.status_code == 201

        # Try to book overlapping session - should fail
        resp2 = await auth_client.post(
            f"/api/v1/sessions/{session2_id}/bookings",
            json={"role": "PLAYER"},
        )
        assert resp2.status_code == 409
        assert "overlapping" in resp2.json()["detail"].lower()

    async def test_non_overlapping_booking_allowed(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Booking non-overlapping sessions succeeds."""
        # Create two non-overlapping sessions
        session1_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T14:00:00Z",
            "2026-07-01T15:00:00Z",
            "Morning Session",
        )
        session2_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T16:00:00Z",  # No overlap
            "2026-07-01T17:00:00Z",
            "Afternoon Session",
        )

        # Book both sessions
        resp1 = await auth_client.post(
            f"/api/v1/sessions/{session1_id}/bookings",
            json={"role": "PLAYER"},
        )
        assert resp1.status_code == 201

        resp2 = await auth_client.post(
            f"/api/v1/sessions/{session2_id}/bookings",
            json={"role": "PLAYER"},
        )
        assert resp2.status_code == 201

    async def test_cancelled_booking_allows_new_overlapping(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """After cancelling, user can book overlapping session."""
        # Create two overlapping sessions by different GMs
        session1_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T14:00:00Z",
            "2026-07-01T16:00:00Z",
            "Session 1",
        )
        session2_id = await self._create_validated_session(
            second_auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "2026-07-01T15:00:00Z",
            "2026-07-01T17:00:00Z",
            "Session 2",
        )

        # Book first session
        resp1 = await auth_client.post(
            f"/api/v1/sessions/{session1_id}/bookings",
            json={"role": "PLAYER"},
        )
        booking1_id = resp1.json()["id"]

        # Cancel first booking
        await auth_client.delete(f"/api/v1/sessions/bookings/{booking1_id}")

        # Now overlapping session should be bookable
        resp2 = await auth_client.post(
            f"/api/v1/sessions/{session2_id}/bookings",
            json={"role": "PLAYER"},
        )
        assert resp2.status_code == 201


class TestNoShow:
    """Tests for no-show functionality."""

    async def _create_validated_session(
        self,
        auth_client: AsyncClient,
        exhibition_id: str,
        time_slot_id: str,
        game_id: str,
    ) -> str:
        """Helper to create a validated session."""
        payload = {
            "title": "No-Show Test Session",
            "exhibition_id": exhibition_id,
            "time_slot_id": time_slot_id,
            "game_id": game_id,
            "max_players_count": 2,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]

        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        return session_id

    async def test_mark_no_show_success(
        self,
        auth_client: AsyncClient,
        client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
        test_user: dict,
    ):
        """GM can mark confirmed booking as no-show."""
        session_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
        )

        # User books the session
        booking_resp = await client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
            headers={"X-User-ID": test_user["id"]},
        )
        booking_id = booking_resp.json()["id"]
        assert booking_resp.json()["status"] == "CONFIRMED"

        # GM (session creator) marks as no-show
        response = await auth_client.post(
            f"/api/v1/sessions/bookings/{booking_id}/no-show"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "NO_SHOW"

    async def test_no_show_promotes_waitlist(
        self,
        auth_client: AsyncClient,
        client: AsyncClient,
        db_session: AsyncSession,
        test_exhibition_with_slot: dict,
        test_game: dict,
        test_user: dict,
    ):
        """Marking no-show promotes next person from waitlist."""
        session_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
        )

        # Fill up the session (max 2 players)
        # First booking by organizer
        booking1_resp = await auth_client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
        )
        booking1_id = booking1_resp.json()["id"]

        # Second booking by test_user
        await client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
            headers={"X-User-ID": test_user["id"]},
        )

        # Create a third user for waitlist
        from app.domain.user.entity import User
        from app.domain.shared.entity import GlobalRole
        from uuid import uuid4

        waitlist_user = User(
            id=uuid4(),
            email="waitlist@example.com",
            hashed_password="hashed_password",
            full_name="Waitlist User",
            global_role=GlobalRole.USER,
            is_active=True,
        )
        db_session.add(waitlist_user)
        await db_session.commit()
        await db_session.refresh(waitlist_user)

        # Third booking goes to waitlist
        booking3_resp = await client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
            headers={"X-User-ID": str(waitlist_user.id)},
        )
        booking3_id = booking3_resp.json()["id"]
        assert booking3_resp.json()["status"] == "WAITING_LIST"

        # Mark first booking as no-show
        await auth_client.post(f"/api/v1/sessions/bookings/{booking1_id}/no-show")

        # Check waitlist person was promoted
        check_resp = await client.get(f"/api/v1/sessions/{session_id}/bookings")
        bookings = check_resp.json()

        # Find the waitlist user's booking
        waitlist_booking = next(
            b for b in bookings if b["id"] == booking3_id
        )
        assert waitlist_booking["status"] == "CONFIRMED"

    async def test_no_show_only_by_gm_or_organizer(
        self,
        auth_client: AsyncClient,
        client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
        test_user: dict,
    ):
        """Regular user cannot mark someone else as no-show."""
        session_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
        )

        # Organizer books
        booking_resp = await auth_client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
        )
        booking_id = booking_resp.json()["id"]

        # Regular user tries to mark as no-show - should fail
        response = await client.post(
            f"/api/v1/sessions/bookings/{booking_id}/no-show",
            headers={"X-User-ID": test_user["id"]},
        )

        assert response.status_code == 403

    async def test_no_show_invalid_status(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Cannot mark cancelled booking as no-show."""
        session_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
        )

        # Book and cancel
        booking_resp = await auth_client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
        )
        booking_id = booking_resp.json()["id"]
        await auth_client.delete(f"/api/v1/sessions/bookings/{booking_id}")

        # Try to mark as no-show
        response = await auth_client.post(
            f"/api/v1/sessions/bookings/{booking_id}/no-show"
        )

        assert response.status_code == 400


class TestGMScheduleOverlap:
    """Tests for GM schedule overlap detection (Issue #22)."""

    async def test_gm_cannot_create_overlapping_sessions(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """GM cannot create a session that overlaps with another they're running."""
        # Create first session and submit for moderation
        payload1 = {
            "title": "First GM Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T16:00:00Z",
        }
        resp1 = await auth_client.post("/api/v1/sessions/", json=payload1)
        session1_id = resp1.json()["id"]

        # Submit first session (makes it count for overlap check)
        await auth_client.post(f"/api/v1/sessions/{session1_id}/submit")

        # Try to create overlapping session - should fail
        payload2 = {
            "title": "Overlapping GM Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T15:00:00Z",  # Overlaps
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        resp2 = await auth_client.post("/api/v1/sessions/", json=payload2)

        assert resp2.status_code == 409
        assert "running session" in resp2.json()["detail"].lower()

    async def test_gm_can_create_non_overlapping_sessions(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """GM can create multiple non-overlapping sessions."""
        # Create first session
        payload1 = {
            "title": "Morning Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T15:00:00Z",
        }
        resp1 = await auth_client.post("/api/v1/sessions/", json=payload1)
        session1_id = resp1.json()["id"]
        await auth_client.post(f"/api/v1/sessions/{session1_id}/submit")

        # Create non-overlapping session - should succeed
        payload2 = {
            "title": "Afternoon Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T16:00:00Z",  # No overlap
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        resp2 = await auth_client.post("/api/v1/sessions/", json=payload2)

        assert resp2.status_code == 201

    async def test_gm_draft_sessions_dont_block(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Draft sessions don't block creation of overlapping sessions."""
        # Create first session but don't submit (stays DRAFT)
        payload1 = {
            "title": "Draft Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T16:00:00Z",
        }
        await auth_client.post("/api/v1/sessions/", json=payload1)
        # Note: NOT submitting, so it stays DRAFT

        # Create overlapping session - should succeed (draft doesn't block)
        payload2 = {
            "title": "Overlapping Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T15:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        resp2 = await auth_client.post("/api/v1/sessions/", json=payload2)

        assert resp2.status_code == 201

    async def test_gm_cannot_propose_if_registered_as_player(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """GM cannot create session if registered as player for overlapping session."""
        # Create and validate a session by ANOTHER GM
        payload1 = {
            "title": "Other GM Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T16:00:00Z",
        }
        resp1 = await second_auth_client.post("/api/v1/sessions/", json=payload1)
        session1_id = resp1.json()["id"]
        await second_auth_client.post(f"/api/v1/sessions/{session1_id}/submit")
        await second_auth_client.post(
            f"/api/v1/sessions/{session1_id}/moderate",
            json={"action": "approve"},
        )

        # First organizer registers as a player for that session
        await auth_client.post(
            f"/api/v1/sessions/{session1_id}/bookings",
            json={"role": "PLAYER"},
        )

        # First organizer tries to create an overlapping session as GM - should fail
        payload2 = {
            "title": "Conflicting GM Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T15:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        resp2 = await auth_client.post("/api/v1/sessions/", json=payload2)

        assert resp2.status_code == 409
        assert "registered as a player" in resp2.json()["detail"].lower()

    async def test_update_session_schedule_checks_overlap(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Updating session schedule checks for GM overlap."""
        # Create two sessions with no overlap
        payload1 = {
            "title": "First Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T15:00:00Z",
        }
        resp1 = await auth_client.post("/api/v1/sessions/", json=payload1)
        session1_id = resp1.json()["id"]
        await auth_client.post(f"/api/v1/sessions/{session1_id}/submit")

        payload2 = {
            "title": "Second Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T16:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        resp2 = await auth_client.post("/api/v1/sessions/", json=payload2)
        session2_id = resp2.json()["id"]

        # Try to update second session to overlap with first - should fail
        update_resp = await auth_client.put(
            f"/api/v1/sessions/{session2_id}",
            json={
                "scheduled_start": "2026-07-01T14:30:00Z",  # Would overlap
                "scheduled_end": "2026-07-01T16:00:00Z",
            },
        )

        assert update_resp.status_code == 409


class TestAgeVerification:
    """Tests for minimum age verification on bookings (Issue #23)."""

    async def _create_validated_session_with_age(
        self,
        auth_client: AsyncClient,
        exhibition_id: str,
        time_slot_id: str,
        game_id: str,
        min_age: int,
    ) -> str:
        """Helper to create a validated session with age requirement."""
        payload = {
            "title": "Adult Session",
            "exhibition_id": exhibition_id,
            "time_slot_id": time_slot_id,
            "game_id": game_id,
            "max_players_count": 4,
            "min_age": min_age,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]

        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        return session_id

    async def test_booking_requires_birth_date_for_age_restricted_session(
        self,
        auth_client: AsyncClient,
        client: AsyncClient,
        db_session: AsyncSession,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Booking age-restricted session without birth_date returns 400."""
        from app.domain.user.entity import User
        from app.domain.shared.entity import GlobalRole

        # Create user without birth_date
        user_no_age = User(
            id=uuid4(),
            email="noage@example.com",
            hashed_password="hashed_password",
            full_name="No Age User",
            global_role=GlobalRole.USER,
            is_active=True,
            birth_date=None,
        )
        db_session.add(user_no_age)
        await db_session.commit()
        await db_session.refresh(user_no_age)

        session_id = await self._create_validated_session_with_age(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            min_age=18,
        )

        # Try to book without birth_date
        response = await client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
            headers={"X-User-ID": str(user_no_age.id)},
        )

        assert response.status_code == 400
        assert "birth date" in response.json()["detail"].lower()

    async def test_booking_rejected_if_too_young(
        self,
        auth_client: AsyncClient,
        client: AsyncClient,
        db_session: AsyncSession,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Booking age-restricted session when too young returns 403."""
        from app.domain.user.entity import User
        from app.domain.shared.entity import GlobalRole
        from datetime import date

        # Create user who is 16 years old
        user_young = User(
            id=uuid4(),
            email="young@example.com",
            hashed_password="hashed_password",
            full_name="Young User",
            global_role=GlobalRole.USER,
            is_active=True,
            birth_date=date(2010, 1, 1),  # 16 years old in 2026
        )
        db_session.add(user_young)
        await db_session.commit()
        await db_session.refresh(user_young)

        session_id = await self._create_validated_session_with_age(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            min_age=18,
        )

        # Try to book when too young
        response = await client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
            headers={"X-User-ID": str(user_young.id)},
        )

        assert response.status_code == 403
        assert "18 years old" in response.json()["detail"]

    async def test_booking_allowed_if_old_enough(
        self,
        auth_client: AsyncClient,
        client: AsyncClient,
        db_session: AsyncSession,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Booking age-restricted session when old enough succeeds."""
        from app.domain.user.entity import User
        from app.domain.shared.entity import GlobalRole
        from datetime import date

        # Create user who is 25 years old
        user_adult = User(
            id=uuid4(),
            email="adult@example.com",
            hashed_password="hashed_password",
            full_name="Adult User",
            global_role=GlobalRole.USER,
            is_active=True,
            birth_date=date(2001, 1, 1),  # 25 years old in 2026
        )
        db_session.add(user_adult)
        await db_session.commit()
        await db_session.refresh(user_adult)

        session_id = await self._create_validated_session_with_age(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            min_age=18,
        )

        # Book when old enough
        response = await client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
            headers={"X-User-ID": str(user_adult.id)},
        )

        assert response.status_code == 201
        assert response.json()["status"] == "CONFIRMED"

    async def test_booking_no_age_check_for_all_ages_session(
        self,
        auth_client: AsyncClient,
        client: AsyncClient,
        db_session: AsyncSession,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Booking session without min_age skips age verification."""
        from app.domain.user.entity import User
        from app.domain.shared.entity import GlobalRole

        # Create user without birth_date
        user_no_age = User(
            id=uuid4(),
            email="noage2@example.com",
            hashed_password="hashed_password",
            full_name="No Age User 2",
            global_role=GlobalRole.USER,
            is_active=True,
            birth_date=None,
        )
        db_session.add(user_no_age)
        await db_session.commit()
        await db_session.refresh(user_no_age)

        # Create session without age requirement
        payload = {
            "title": "All Ages Session",
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
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        # Book without birth_date - should succeed (no age requirement)
        response = await client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
            headers={"X-User-ID": str(user_no_age.id)},
        )

        assert response.status_code == 201


class TestSessionDiscovery:
    """Tests for session discovery with advanced filters (JS.C1, JS.C6)."""

    async def _create_validated_session(
        self,
        auth_client: AsyncClient,
        exhibition_id: str,
        time_slot_id: str,
        game_id: str,
        title: str = "Test Session",
        language: str = "en",
        min_age: int = None,
        is_accessible: bool = False,
    ) -> str:
        """Helper to create a validated session with options."""
        payload = {
            "title": title,
            "exhibition_id": exhibition_id,
            "time_slot_id": time_slot_id,
            "game_id": game_id,
            "max_players_count": 4,
            "language": language,
            "is_accessible_disability": is_accessible,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        if min_age is not None:
            payload["min_age"] = min_age

        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]

        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        return session_id

    async def test_search_returns_validated_sessions(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Search only returns validated sessions."""
        # Create a draft session (don't submit)
        draft_payload = {
            "title": "Draft Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T15:00:00Z",
        }
        await auth_client.post("/api/v1/sessions/", json=draft_payload)

        # Create a validated session
        await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "Validated Session",
        )

        # Search should only return validated
        response = await auth_client.get(
            "/api/v1/sessions/search",
            params={"exhibition_id": test_exhibition_with_slot["exhibition_id"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Validated Session"

    async def test_search_filter_by_language(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Search can filter by language."""
        # Create English session
        await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "English Session",
            language="en",
        )

        # Create French session (different GM to avoid overlap)
        await self._create_validated_session(
            second_auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "French Session",
            language="fr",
        )

        # Filter by French
        response = await auth_client.get(
            "/api/v1/sessions/search",
            params={
                "exhibition_id": test_exhibition_with_slot["exhibition_id"],
                "language": "fr",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "French Session"
        assert data[0]["language"] == "fr"

    async def test_search_filter_by_accessibility(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Search can filter by accessibility."""
        # Create accessible session
        await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "Accessible Session",
            is_accessible=True,
        )

        # Create non-accessible session
        await self._create_validated_session(
            second_auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "Regular Session",
            is_accessible=False,
        )

        # Filter accessible only
        response = await auth_client.get(
            "/api/v1/sessions/search",
            params={
                "exhibition_id": test_exhibition_with_slot["exhibition_id"],
                "is_accessible_disability": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Accessible Session"
        assert data[0]["is_accessible_disability"] is True

    async def test_search_filter_by_age(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Search can filter by age requirement."""
        # Create all-ages session
        await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "All Ages Session",
            min_age=None,
        )

        # Create 18+ session
        await self._create_validated_session(
            second_auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "Adult Session",
            min_age=18,
        )

        # Filter for 16 year old - should only see all-ages
        response = await auth_client.get(
            "/api/v1/sessions/search",
            params={
                "exhibition_id": test_exhibition_with_slot["exhibition_id"],
                "max_age_requirement": 16,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "All Ages Session"

        # Filter for 18+ - should see both
        response2 = await auth_client.get(
            "/api/v1/sessions/search",
            params={
                "exhibition_id": test_exhibition_with_slot["exhibition_id"],
                "max_age_requirement": 18,
            },
        )
        assert len(response2.json()) == 2

    async def test_search_filter_available_seats(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        client: AsyncClient,
        db_session: AsyncSession,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Search can filter by seat availability."""
        from app.domain.user.entity import User
        from app.domain.shared.entity import GlobalRole

        # Create a third user to fill the session
        filler_user = User(
            id=uuid4(),
            email="filler@example.com",
            hashed_password="hashed_password",
            full_name="Filler User",
            global_role=GlobalRole.USER,
            is_active=True,
        )
        db_session.add(filler_user)
        await db_session.commit()
        await db_session.refresh(filler_user)

        # Create session with 2 seats by first GM
        payload = {
            "title": "Small Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 2,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T15:00:00Z",
        }
        resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session1_id = resp.json()["id"]
        await auth_client.post(f"/api/v1/sessions/{session1_id}/submit")
        await auth_client.post(
            f"/api/v1/sessions/{session1_id}/moderate",
            json={"action": "approve"},
        )

        # Fill up the session with two other users
        await second_auth_client.post(
            f"/api/v1/sessions/{session1_id}/bookings",
            json={"role": "PLAYER"},
        )
        await client.post(
            f"/api/v1/sessions/{session1_id}/bookings",
            json={"role": "PLAYER"},
            headers={"X-User-ID": str(filler_user.id)},
        )

        # Create another session with available seats (later time to avoid overlap)
        payload2 = {
            "title": "Available Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T16:00:00Z",
            "scheduled_end": "2026-07-01T18:00:00Z",
        }
        resp2 = await second_auth_client.post("/api/v1/sessions/", json=payload2)
        session2_id = resp2.json()["id"]
        await second_auth_client.post(f"/api/v1/sessions/{session2_id}/submit")
        await second_auth_client.post(
            f"/api/v1/sessions/{session2_id}/moderate",
            json={"action": "approve"},
        )

        # Filter for available seats only
        response = await auth_client.get(
            "/api/v1/sessions/search",
            params={
                "exhibition_id": test_exhibition_with_slot["exhibition_id"],
                "has_available_seats": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Available Session"
        assert data[0]["available_seats"] > 0

    async def test_search_returns_computed_fields(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
        test_game_category: dict,
    ):
        """Search returns computed fields like available_seats, category_slug."""
        await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "Test Session",
        )

        response = await auth_client.get(
            "/api/v1/sessions/search",
            params={"exhibition_id": test_exhibition_with_slot["exhibition_id"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        session = data[0]
        assert "available_seats" in session
        assert session["available_seats"] == 4  # max_players_count
        assert "category_slug" in session
        assert session["category_slug"] == "rpg"
        assert "game_title" in session
        assert session["game_title"] == "Dungeons & Dragons 5e"


class TestSessionCancellation:
    """Tests for session cancellation (JS.B4)."""

    async def _create_validated_session(
        self,
        auth_client: AsyncClient,
        exhibition_id: str,
        time_slot_id: str,
        game_id: str,
        title: str = "Test Session",
    ) -> str:
        """Helper to create a validated session."""
        payload = {
            "title": title,
            "exhibition_id": exhibition_id,
            "time_slot_id": time_slot_id,
            "game_id": game_id,
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = resp.json()["id"]

        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        return session_id

    async def test_cancel_session_no_bookings(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Cancel a session without bookings returns success."""
        session_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
        )

        response = await auth_client.post(
            f"/api/v1/sessions/{session_id}/cancel",
            json={"reason": "GM is sick"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session"]["status"] == "CANCELLED"
        assert data["session"]["rejection_reason"] == "GM is sick"
        assert data["affected_users"] == []
        assert data["notifications_sent"] == 0

    async def test_cancel_session_with_bookings(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Cancel a session with bookings notifies affected users."""
        # Create session as second organizer
        session_id = await self._create_validated_session(
            second_auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
        )

        # Book as first user
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
        )

        # Cancel as session creator (second organizer)
        response = await second_auth_client.post(
            f"/api/v1/sessions/{session_id}/cancel",
            json={"reason": "Emergency cancellation"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session"]["status"] == "CANCELLED"
        assert len(data["affected_users"]) == 1
        # affected_users shows ORIGINAL status (what they were before cancellation)
        assert data["affected_users"][0]["booking_status"] == "CONFIRMED"
        assert data["notifications_sent"] == 1

    async def test_cancel_session_forbidden_for_regular_user(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
        test_user: dict,
    ):
        """Regular user cannot cancel a session they don't own."""
        # Create session as second organizer
        session_id = await self._create_validated_session(
            second_auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
        )

        # Try to cancel as regular user (not an organizer)
        from httpx import AsyncClient as HttpxClient
        from httpx import ASGITransport
        from app.main import app

        async with HttpxClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-ID": test_user["id"]},
        ) as user_client:
            response = await user_client.post(
                f"/api/v1/sessions/{session_id}/cancel",
                json={"reason": "Should not work"},
            )

        assert response.status_code == 403

    async def test_cancel_already_cancelled_session(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Cannot cancel an already cancelled session."""
        session_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
        )

        # Cancel once
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/cancel",
            json={"reason": "First cancellation"},
        )

        # Try to cancel again
        response = await auth_client.post(
            f"/api/v1/sessions/{session_id}/cancel",
            json={"reason": "Second attempt"},
        )

        assert response.status_code == 400
        assert "already cancelled" in response.json()["detail"]

    async def test_cancel_session_not_found(
        self,
        auth_client: AsyncClient,
    ):
        """Cancel non-existent session returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await auth_client.post(
            f"/api/v1/sessions/{fake_id}/cancel",
            json={"reason": "Does not exist"},
        )

        assert response.status_code == 404

    async def test_cancel_cancels_waitlist_bookings(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Cancel a session also cancels waitlist bookings."""
        # Create session with 1 max player as second organizer
        payload = {
            "title": "Small Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 1,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        resp = await second_auth_client.post("/api/v1/sessions/", json=payload)
        session_id = resp.json()["id"]

        await second_auth_client.post(f"/api/v1/sessions/{session_id}/submit")
        await second_auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        # Book as first user (confirmed)
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
        )

        # Second booking would go to waitlist - but second_auth_client is the GM
        # so we only have 1 booking

        # Cancel as GM
        response = await second_auth_client.post(
            f"/api/v1/sessions/{session_id}/cancel",
            json={"reason": "Cancelling small session"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["affected_users"]) == 1
        # affected_users shows ORIGINAL status (CONFIRMED in this case)
        assert data["affected_users"][0]["booking_status"] == "CONFIRMED"


class TestDelegatedModeration:
    """Tests for delegated moderation by zone partners (#32)."""

    async def test_partner_can_moderate_session_in_delegated_zone(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
        test_organizer: dict,
        db_session,
    ):
        """Partner managing a zone can moderate sessions on tables in that zone."""
        from uuid import uuid4
        from app.domain.exhibition.entity import Zone, PhysicalTable
        from app.domain.organization.entity import UserGroup
        from app.domain.user.entity import UserGroupMembership
        from app.domain.shared.entity import ZoneType, PhysicalTableStatus, GroupRole

        # Create a partner group using the actual organization
        partner_group = UserGroup(
            id=uuid4(),
            organization_id=test_organizer["organization_id"],
            name="Partner Group",
            type="STAFF",
            is_public=False,
        )
        db_session.add(partner_group)

        # Get second organizer's user ID (they will be the partner)
        # second_auth_client uses second_organizer fixture
        second_organizer_resp = await second_auth_client.get("/api/v1/users/me")
        second_organizer_id = second_organizer_resp.json()["id"]

        # Add second organizer to partner group
        membership = UserGroupMembership(
            id=uuid4(),
            user_id=second_organizer_id,
            user_group_id=partner_group.id,
            group_role=GroupRole.MEMBER,
        )
        db_session.add(membership)

        # Create a zone delegated to the partner group
        zone = Zone(
            id=uuid4(),
            exhibition_id=test_exhibition_with_slot["exhibition_id"],
            name="Partner Zone",
            type=ZoneType.RPG,
            delegated_to_group_id=partner_group.id,
        )
        db_session.add(zone)

        # Create a table in the zone
        table = PhysicalTable(
            id=uuid4(),
            zone_id=zone.id,
            label="P1",
            capacity=6,
            status=PhysicalTableStatus.AVAILABLE,
        )
        db_session.add(table)
        await db_session.commit()

        # Create a session (as first organizer) and assign to the table
        payload = {
            "title": "Partner Zone Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]

        # Assign table to session
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/assign-table",
            params={"table_id": str(table.id)},
        )

        # Submit for moderation
        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")

        # Partner (second organizer) should be able to moderate
        response = await second_auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "VALIDATED"


class TestSessionCopy:
    """Tests for session copy/duplicate (#33)."""

    async def test_copy_session_basic(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Copy a session creates a new draft with same properties."""
        # Create original session
        payload = {
            "title": "Original Session",
            "description": "A great adventure",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 5,
            "language": "fr",
            "min_age": 12,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]

        # Copy the session
        response = await auth_client.post(f"/api/v1/sessions/{session_id}/copy")

        assert response.status_code == 201
        data = response.json()
        assert data["id"] != session_id
        assert data["title"] == "Copy of Original Session"
        assert data["description"] == "A great adventure"
        assert data["max_players_count"] == 5
        assert data["language"] == "fr"
        assert data["min_age"] == 12
        assert data["status"] == "DRAFT"

    async def test_copy_session_custom_title(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Copy with custom title uses provided title."""
        payload = {
            "title": "Original",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]

        response = await auth_client.post(
            f"/api/v1/sessions/{session_id}/copy",
            json={"title": "My Custom Copy"},
        )

        assert response.status_code == 201
        assert response.json()["title"] == "My Custom Copy"

    async def test_copy_session_not_found(
        self,
        auth_client: AsyncClient,
    ):
        """Copy non-existent session returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await auth_client.post(f"/api/v1/sessions/{fake_id}/copy")

        assert response.status_code == 404

    async def test_copy_session_forbidden_for_other_user(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
        test_user: dict,
    ):
        """Regular user cannot copy someone else's session."""
        # Create session as second organizer
        payload = {
            "title": "Other's Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await second_auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]

        # Try to copy as regular user
        from httpx import AsyncClient as HttpxClient
        from httpx import ASGITransport
        from app.main import app

        async with HttpxClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-ID": test_user["id"]},
        ) as user_client:
            response = await user_client.post(f"/api/v1/sessions/{session_id}/copy")

        assert response.status_code == 403


class TestModerationDialogue:
    """Tests for moderation dialogue endpoints (#30)."""

    async def test_request_changes_workflow(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Moderator can request changes, which adds a comment."""
        # Create and submit session
        payload = {
            "title": "Needs Changes",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=payload)
        session_id = create_resp.json()["id"]

        # Submit for moderation
        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")

        # Request changes
        response = await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "request_changes", "comment": "Please add safety tools"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "CHANGES_REQUESTED"

        # Check that comment was created
        comments_resp = await auth_client.get(f"/api/v1/sessions/{session_id}/comments")
        assert comments_resp.status_code == 200
        comments = comments_resp.json()
        assert len(comments) == 1
        assert comments[0]["content"] == "Please add safety tools"

    async def test_resubmit_after_changes_requested(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Proposer can resubmit after making requested changes."""
        # Create, submit, and get changes requested
        payload = {
            "title": "Will Update",
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
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "request_changes", "comment": "Add description"},
        )

        # Update session
        await auth_client.put(
            f"/api/v1/sessions/{session_id}",
            json={"description": "Added description as requested"},
        )

        # Resubmit
        response = await auth_client.post(f"/api/v1/sessions/{session_id}/submit")

        assert response.status_code == 200
        assert response.json()["status"] == "PENDING_MODERATION"

    async def test_add_comment_to_moderation_thread(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Users can add comments during moderation."""
        # Create and submit session
        payload = {
            "title": "Discussion Session",
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

        # Add comment
        response = await auth_client.post(
            f"/api/v1/sessions/{session_id}/comments",
            json={"content": "I'd like to clarify the format"},
        )

        assert response.status_code == 201
        assert response.json()["content"] == "I'd like to clarify the format"
        assert "user_full_name" in response.json()

    async def test_list_comments_chronological(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Comments are listed in chronological order."""
        # Create and submit session
        payload = {
            "title": "Multi Comment Session",
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

        # Add multiple comments
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/comments",
            json={"content": "First comment"},
        )
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/comments",
            json={"content": "Second comment"},
        )

        # List comments
        response = await auth_client.get(f"/api/v1/sessions/{session_id}/comments")

        assert response.status_code == 200
        comments = response.json()
        assert len(comments) == 2
        assert comments[0]["content"] == "First comment"
        assert comments[1]["content"] == "Second comment"

    async def test_cannot_comment_on_validated_session(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Cannot add comments after session is validated."""
        # Create, submit, and approve session
        payload = {
            "title": "Approved Session",
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
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        # Try to add comment
        response = await auth_client.post(
            f"/api/v1/sessions/{session_id}/comments",
            json={"content": "Too late!"},
        )

        assert response.status_code == 400

    async def test_request_changes_requires_comment(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """request_changes action requires a comment."""
        # Create and submit session
        payload = {
            "title": "Missing Comment",
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

        # Try request_changes without comment
        response = await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "request_changes"},
        )

        assert response.status_code == 422
