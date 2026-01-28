"""
Tests for Operations API endpoints.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.game.entity import GameCategory, Game, GameSession
from app.domain.shared.entity import GameComplexity, SessionStatus


@pytest.fixture
async def test_game_category(db_session: AsyncSession) -> dict:
    """Create a test game category."""
    category = GameCategory(
        id=uuid4(),
        name="Role-Playing Games",
        slug="rpg-ops",
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
        title="Test RPG",
        publisher="Test Publisher",
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
async def ops_exhibition_setup(auth_client: AsyncClient, test_organizer: dict) -> dict:
    """Create an exhibition with zones, tables, and time slots for operations tests."""
    from datetime import timezone
    # Use current time for the exhibition to allow testing with "now" times
    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(hours=2)).isoformat()
    end_date = (now + timedelta(days=2)).isoformat()
    slot_start = (now - timedelta(hours=1)).isoformat()
    slot_end = (now + timedelta(hours=5)).isoformat()

    # Create exhibition with 15 min grace period
    exhibition_payload = {
        "title": "Ops Test Convention",
        "slug": "ops-test-convention-" + str(uuid4())[:8],
        "start_date": start_date,
        "end_date": end_date,
        "organization_id": test_organizer["organization_id"],
        "grace_period_minutes": 15,
    }
    exhibition_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
    exhibition_id = exhibition_resp.json()["id"]

    # Create time slot spanning current time
    slot_payload = {
        "name": "Current Slot",
        "start_time": slot_start,
        "end_time": slot_end,
        "max_duration_minutes": 360,
        "buffer_time_minutes": 15,
    }
    slot_resp = await auth_client.post(
        f"/api/v1/exhibitions/{exhibition_id}/slots", json=slot_payload
    )
    time_slot_id = slot_resp.json()["id"]

    # Create zone with tables
    zone_payload = {"name": "Main Hall", "exhibition_id": exhibition_id}
    zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
    zone_id = zone_resp.json()["id"]

    tables_resp = await auth_client.post(
        f"/api/v1/zones/{zone_id}/batch-tables",
        json={"prefix": "T", "count": 5},
    )
    tables = tables_resp.json()["tables"]

    return {
        "exhibition_id": exhibition_id,
        "time_slot_id": time_slot_id,
        "zone_id": zone_id,
        "tables": tables,
        "slot_start": slot_start,
        "slot_end": slot_end,
    }


class TestAvailableTables:
    """Tests for GET /api/v1/ops/exhibitions/{id}/available-tables"""

    async def test_all_tables_available_when_no_sessions(
        self,
        auth_client: AsyncClient,
        ops_exhibition_setup: dict,
    ):
        """All tables available when no sessions are running."""
        response = await auth_client.get(
            f"/api/v1/ops/exhibitions/{ops_exhibition_setup['exhibition_id']}/available-tables"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # All 5 tables

    async def test_table_unavailable_during_session(
        self,
        auth_client: AsyncClient,
        ops_exhibition_setup: dict,
        test_game: dict,
    ):
        """Table is not available when session is running on it."""
        from datetime import timezone
        # Create and validate a session
        now = datetime.now(timezone.utc)
        session_payload = {
            "title": "Occupied Table Test",
            "exhibition_id": ops_exhibition_setup["exhibition_id"],
            "time_slot_id": ops_exhibition_setup["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": (now - timedelta(minutes=30)).isoformat(),
            "scheduled_end": (now + timedelta(hours=1)).isoformat(),
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=session_payload)
        session_id = create_resp.json()["id"]

        # Submit and approve
        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        # Assign table
        table_id = ops_exhibition_setup["tables"][0]["id"]
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/assign-table",
            params={"table_id": table_id},
        )

        # Check available tables - should be 4 now
        response = await auth_client.get(
            f"/api/v1/ops/exhibitions/{ops_exhibition_setup['exhibition_id']}/available-tables"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        # The occupied table should not be in the list
        table_ids = [t["id"] for t in data]
        assert table_id not in table_ids


class TestAutoCancel:
    """Tests for POST /api/v1/ops/exhibitions/{id}/auto-cancel"""

    async def test_auto_cancel_no_show_session(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        ops_exhibition_setup: dict,
        test_game: dict,
    ):
        """Session is cancelled when GM doesn't check in after grace period."""
        from datetime import timezone
        # Create a session that started 20 minutes ago (grace period is 15)
        now = datetime.now(timezone.utc)
        past_start = now - timedelta(minutes=20)
        session_payload = {
            "title": "No Show Session",
            "exhibition_id": ops_exhibition_setup["exhibition_id"],
            "time_slot_id": ops_exhibition_setup["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": past_start.isoformat(),
            "scheduled_end": (past_start + timedelta(hours=2)).isoformat(),
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=session_payload)
        session_id = create_resp.json()["id"]

        # Submit and approve
        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        # Trigger auto-cancel
        response = await auth_client.post(
            f"/api/v1/ops/exhibitions/{ops_exhibition_setup['exhibition_id']}/auto-cancel"
        )

        assert response.status_code == 200
        cancelled = response.json()
        assert len(cancelled) == 1
        assert cancelled[0]["id"] == session_id
        assert cancelled[0]["status"] == "CANCELLED"

    async def test_auto_cancel_does_not_affect_checked_in_sessions(
        self,
        auth_client: AsyncClient,
        ops_exhibition_setup: dict,
        test_game: dict,
    ):
        """Sessions where GM checked in are not cancelled."""
        from datetime import timezone
        # Create a session that started 20 minutes ago
        now = datetime.now(timezone.utc)
        past_start = now - timedelta(minutes=20)
        session_payload = {
            "title": "Checked In Session",
            "exhibition_id": ops_exhibition_setup["exhibition_id"],
            "time_slot_id": ops_exhibition_setup["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": past_start.isoformat(),
            "scheduled_end": (past_start + timedelta(hours=2)).isoformat(),
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=session_payload)
        session_id = create_resp.json()["id"]

        # Submit and approve
        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        # GM checks in
        await auth_client.post(f"/api/v1/ops/sessions/{session_id}/gm-check-in")

        # Trigger auto-cancel
        response = await auth_client.post(
            f"/api/v1/ops/exhibitions/{ops_exhibition_setup['exhibition_id']}/auto-cancel"
        )

        assert response.status_code == 200
        cancelled = response.json()
        assert len(cancelled) == 0  # Nothing cancelled

    async def test_auto_cancel_forbidden_for_user(
        self,
        auth_client: AsyncClient,
        client: AsyncClient,
        test_user: dict,
        ops_exhibition_setup: dict,
    ):
        """Regular user cannot trigger auto-cancel."""
        response = await client.post(
            f"/api/v1/ops/exhibitions/{ops_exhibition_setup['exhibition_id']}/auto-cancel",
            headers={"X-User-ID": test_user["id"]},
        )

        assert response.status_code == 403


class TestGMCheckIn:
    """Tests for POST /api/v1/ops/sessions/{id}/gm-check-in"""

    async def test_gm_check_in_success(
        self,
        auth_client: AsyncClient,
        ops_exhibition_setup: dict,
        test_game: dict,
    ):
        """GM can check in to their session."""
        from datetime import timezone
        # Create and validate a session
        now = datetime.now(timezone.utc)
        session_payload = {
            "title": "GM Check In Test",
            "exhibition_id": ops_exhibition_setup["exhibition_id"],
            "time_slot_id": ops_exhibition_setup["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": now.isoformat(),
            "scheduled_end": (now + timedelta(hours=2)).isoformat(),
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=session_payload)
        session_id = create_resp.json()["id"]

        # Submit and approve
        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        # GM checks in
        response = await auth_client.post(f"/api/v1/ops/sessions/{session_id}/gm-check-in")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"
        assert data["gm_checked_in_at"] is not None

    async def test_gm_check_in_forbidden_for_other_user(
        self,
        auth_client: AsyncClient,
        client: AsyncClient,
        test_user: dict,
        ops_exhibition_setup: dict,
        test_game: dict,
    ):
        """Other user cannot check in for a session they don't own."""
        from datetime import timezone
        # Create and validate a session (as organizer)
        now = datetime.now(timezone.utc)
        session_payload = {
            "title": "Forbidden Check In Test",
            "exhibition_id": ops_exhibition_setup["exhibition_id"],
            "time_slot_id": ops_exhibition_setup["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": now.isoformat(),
            "scheduled_end": (now + timedelta(hours=2)).isoformat(),
        }
        create_resp = await auth_client.post("/api/v1/sessions/", json=session_payload)
        session_id = create_resp.json()["id"]

        # Submit and approve
        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/moderate",
            json={"action": "approve"},
        )

        # Other user tries to check in
        response = await client.post(
            f"/api/v1/ops/sessions/{session_id}/gm-check-in",
            headers={"X-User-ID": test_user["id"]},
        )

        assert response.status_code == 403

    async def test_gm_check_in_not_found(
        self,
        auth_client: AsyncClient,
    ):
        """Check in for non-existent session returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await auth_client.post(f"/api/v1/ops/sessions/{fake_id}/gm-check-in")

        assert response.status_code == 404
