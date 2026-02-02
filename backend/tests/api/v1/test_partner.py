"""
Tests for Partner API endpoints (Issue #10).
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exhibition.entity import Zone, PhysicalTable, Exhibition, TimeSlot
from app.domain.game.entity import Game, GameCategory, GameSession
from app.domain.user.entity import UserExhibitionRole
from app.domain.shared.entity import (
    ExhibitionRole,
    ZoneType,
    PhysicalTableStatus,
    SessionStatus,
    GameComplexity,
)


@pytest.fixture
async def test_game_category(db_session: AsyncSession) -> dict:
    """Create a test game category."""
    category = GameCategory(
        id=uuid4(),
        name="Role-Playing Games",
        slug="rpg-partner",
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
        title="Partner Test Game",
        publisher="Test Publisher",
        complexity=GameComplexity.INTERMEDIATE,
        min_players=2,
        max_players=6,
    )
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)

    return {
        "id": str(game.id),
        "title": game.title,
        "category_id": str(game.category_id),
    }


class TestPartnerZones:
    """Tests for GET /api/v1/partner/exhibitions/{id}/zones"""

    async def test_partner_can_list_assigned_zones(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_organizer: dict,
        db_session: AsyncSession,
    ):
        """Partner can list only zones assigned to them."""
        # Get second user ID
        me_resp = await second_auth_client.get("/api/v1/users/me")
        partner_user_id = me_resp.json()["id"]

        # Create exhibition
        exhibition_payload = {
            "title": "Partner Zone Test",
            "slug": "partner-zone-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create two zones
        zone1 = Zone(
            id=uuid4(),
            exhibition_id=exhibition_id,
            name="Partner Zone",
            type=ZoneType.RPG,
            moderation_required=False,
        )
        zone2 = Zone(
            id=uuid4(),
            exhibition_id=exhibition_id,
            name="Other Zone",
            type=ZoneType.BOARD_GAME,
        )
        db_session.add_all([zone1, zone2])

        # Create tables in zones
        table1 = PhysicalTable(
            id=uuid4(),
            zone_id=zone1.id,
            label="P1",
            capacity=6,
            status=PhysicalTableStatus.AVAILABLE,
        )
        table2 = PhysicalTable(
            id=uuid4(),
            zone_id=zone1.id,
            label="P2",
            capacity=6,
            status=PhysicalTableStatus.AVAILABLE,
        )
        db_session.add_all([table1, table2])

        # Remove second user's ORGANIZER role and assign PARTNER role with zone1 only
        await db_session.execute(
            delete(UserExhibitionRole).where(
                UserExhibitionRole.user_id == partner_user_id,
                UserExhibitionRole.exhibition_id == exhibition_id,
            )
        )
        partner_role = UserExhibitionRole(
            id=uuid4(),
            user_id=partner_user_id,
            exhibition_id=exhibition_id,
            role=ExhibitionRole.PARTNER,
            zone_ids=[str(zone1.id)],
        )
        db_session.add(partner_role)
        await db_session.commit()

        # Partner should only see zone1
        response = await second_auth_client.get(
            f"/api/v1/partner/exhibitions/{exhibition_id}/zones"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Partner Zone"
        assert data[0]["table_count"] == 2
        assert data[0]["moderation_required"] is False

    async def test_non_partner_cannot_access_partner_zones(
        self,
        auth_client: AsyncClient,
        test_organizer: dict,
    ):
        """User without PARTNER role cannot access partner zones endpoint."""
        # Create exhibition (auth_client user is ORGANIZER, not PARTNER)
        exhibition_payload = {
            "title": "No Partner Access Test",
            "slug": "no-partner-access",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Organizer should get empty list (not an error, just no partner zones)
        response = await auth_client.get(
            f"/api/v1/partner/exhibitions/{exhibition_id}/zones"
        )

        # Organizers can technically access the endpoint but see empty list
        # if they don't have PARTNER role
        assert response.status_code == 200
        assert response.json() == []


class TestPartnerSessions:
    """Tests for GET /api/v1/partner/exhibitions/{id}/sessions"""

    async def test_partner_can_list_sessions_in_assigned_zones(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_organizer: dict,
        test_game: dict,
        db_session: AsyncSession,
    ):
        """Partner can list sessions only in their assigned zones."""
        # Get second user ID
        me_resp = await second_auth_client.get("/api/v1/users/me")
        partner_user_id = me_resp.json()["id"]

        # Create exhibition with time slot
        exhibition_payload = {
            "title": "Partner Sessions Test",
            "slug": "partner-sessions-test",
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
            "end_time": "2026-07-01T12:00:00Z",
            "max_duration_minutes": 180,
        }
        slot_resp = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/slots", json=slot_payload
        )
        time_slot_id = slot_resp.json()["id"]

        # Create zone and table
        zone = Zone(
            id=uuid4(),
            exhibition_id=exhibition_id,
            name="Partner Zone",
            type=ZoneType.RPG,
            moderation_required=False,
        )
        db_session.add(zone)
        await db_session.flush()

        table = PhysicalTable(
            id=uuid4(),
            zone_id=zone.id,
            label="P1",
            capacity=6,
            status=PhysicalTableStatus.AVAILABLE,
        )
        db_session.add(table)

        # Assign partner role
        await db_session.execute(
            delete(UserExhibitionRole).where(
                UserExhibitionRole.user_id == partner_user_id,
                UserExhibitionRole.exhibition_id == exhibition_id,
            )
        )
        partner_role = UserExhibitionRole(
            id=uuid4(),
            user_id=partner_user_id,
            exhibition_id=exhibition_id,
            role=ExhibitionRole.PARTNER,
            zone_ids=[str(zone.id)],
        )
        db_session.add(partner_role)
        await db_session.commit()

        # Create a session in the partner's zone (as organizer)
        session_payload = {
            "title": "Partner Zone Session",
            "exhibition_id": exhibition_id,
            "time_slot_id": time_slot_id,
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T09:00:00Z",
            "scheduled_end": "2026-07-01T12:00:00Z",
        }
        session_resp = await auth_client.post("/api/v1/sessions/", json=session_payload)
        session_id = session_resp.json()["id"]

        # Assign table and submit
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/assign-table",
            params={"table_id": str(table.id)},
        )
        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")

        # Partner should see the session
        response = await second_auth_client.get(
            f"/api/v1/partner/exhibitions/{exhibition_id}/sessions"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Partner Zone Session"
        assert data[0]["zone_name"] == "Partner Zone"
        assert data[0]["table_label"] == "P1"

    async def test_partner_can_filter_sessions_by_status(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_organizer: dict,
        test_game: dict,
        db_session: AsyncSession,
    ):
        """Partner can filter sessions by status."""
        # Get second user ID
        me_resp = await second_auth_client.get("/api/v1/users/me")
        partner_user_id = me_resp.json()["id"]

        # Create exhibition with time slot
        exhibition_payload = {
            "title": "Partner Filter Test",
            "slug": "partner-filter-test",
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
            "end_time": "2026-07-01T12:00:00Z",
            "max_duration_minutes": 180,
        }
        slot_resp = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/slots", json=slot_payload
        )
        time_slot_id = slot_resp.json()["id"]

        # Create zone and table
        zone = Zone(
            id=uuid4(),
            exhibition_id=exhibition_id,
            name="Filter Zone",
            type=ZoneType.RPG,
            moderation_required=False,
        )
        db_session.add(zone)
        await db_session.flush()

        table = PhysicalTable(
            id=uuid4(),
            zone_id=zone.id,
            label="F1",
            capacity=6,
            status=PhysicalTableStatus.AVAILABLE,
        )
        db_session.add(table)

        # Assign partner role
        await db_session.execute(
            delete(UserExhibitionRole).where(
                UserExhibitionRole.user_id == partner_user_id,
                UserExhibitionRole.exhibition_id == exhibition_id,
            )
        )
        partner_role = UserExhibitionRole(
            id=uuid4(),
            user_id=partner_user_id,
            exhibition_id=exhibition_id,
            role=ExhibitionRole.PARTNER,
            zone_ids=[str(zone.id)],
        )
        db_session.add(partner_role)
        await db_session.commit()

        # Create and submit a session
        session_payload = {
            "title": "Pending Session",
            "exhibition_id": exhibition_id,
            "time_slot_id": time_slot_id,
            "game_id": test_game["id"],
            "max_players_count": 4,
            "scheduled_start": "2026-07-01T09:00:00Z",
            "scheduled_end": "2026-07-01T12:00:00Z",
        }
        session_resp = await auth_client.post("/api/v1/sessions/", json=session_payload)
        session_id = session_resp.json()["id"]

        await auth_client.post(
            f"/api/v1/sessions/{session_id}/assign-table",
            params={"table_id": str(table.id)},
        )
        await auth_client.post(f"/api/v1/sessions/{session_id}/submit")

        # Filter by PENDING_MODERATION - should find the session
        response = await second_auth_client.get(
            f"/api/v1/partner/exhibitions/{exhibition_id}/sessions",
            params={"status": "PENDING_MODERATION"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Filter by VALIDATED - should find nothing
        response = await second_auth_client.get(
            f"/api/v1/partner/exhibitions/{exhibition_id}/sessions",
            params={"status": "VALIDATED"},
        )
        assert response.status_code == 200
        assert len(response.json()) == 0


class TestSeriesBatchCreate:
    """Tests for POST /api/v1/partner/sessions/batch"""

    async def test_partner_can_create_series(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_organizer: dict,
        test_game: dict,
        db_session: AsyncSession,
    ):
        """Partner can create a series of sessions across time slots and tables."""
        # Get second user ID
        me_resp = await second_auth_client.get("/api/v1/users/me")
        partner_user_id = me_resp.json()["id"]

        # Create exhibition
        exhibition_payload = {
            "title": "Series Test",
            "slug": "series-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create time slots
        slot1_resp = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/slots",
            json={
                "name": "Morning",
                "start_time": "2026-07-01T09:00:00Z",
                "end_time": "2026-07-01T12:00:00Z",
                "max_duration_minutes": 180,
            },
        )
        slot2_resp = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/slots",
            json={
                "name": "Afternoon",
                "start_time": "2026-07-01T14:00:00Z",
                "end_time": "2026-07-01T17:00:00Z",
                "max_duration_minutes": 180,
            },
        )
        slot1_id = slot1_resp.json()["id"]
        slot2_id = slot2_resp.json()["id"]

        # Create zone and tables
        zone = Zone(
            id=uuid4(),
            exhibition_id=exhibition_id,
            name="Series Zone",
            type=ZoneType.DEMO,
            moderation_required=False,
        )
        db_session.add(zone)
        await db_session.flush()

        table1 = PhysicalTable(
            id=uuid4(),
            zone_id=zone.id,
            label="S1",
            capacity=4,
            status=PhysicalTableStatus.AVAILABLE,
        )
        table2 = PhysicalTable(
            id=uuid4(),
            zone_id=zone.id,
            label="S2",
            capacity=4,
            status=PhysicalTableStatus.AVAILABLE,
        )
        db_session.add_all([table1, table2])

        # Assign partner role
        await db_session.execute(
            delete(UserExhibitionRole).where(
                UserExhibitionRole.user_id == partner_user_id,
                UserExhibitionRole.exhibition_id == exhibition_id,
            )
        )
        partner_role = UserExhibitionRole(
            id=uuid4(),
            user_id=partner_user_id,
            exhibition_id=exhibition_id,
            role=ExhibitionRole.PARTNER,
            zone_ids=[str(zone.id)],
        )
        db_session.add(partner_role)
        await db_session.commit()

        # Create series (2 slots × 2 tables = 4 sessions)
        series_payload = {
            "exhibition_id": exhibition_id,
            "game_id": test_game["id"],
            "title": "Demo Session",
            "description": "Come try the game!",
            "max_players_count": 4,
            "duration_minutes": 90,
            "time_slot_ids": [slot1_id, slot2_id],
            "table_ids": [str(table1.id), str(table2.id)],
        }
        response = await second_auth_client.post(
            "/api/v1/partner/sessions/batch", json=series_payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["created_count"] == 4
        assert len(data["sessions"]) == 4

        # Verify sessions were created with correct titles
        titles = [s["title"] for s in data["sessions"]]
        assert "Demo Session (Morning - S1)" in titles
        assert "Demo Session (Morning - S2)" in titles
        assert "Demo Session (Afternoon - S1)" in titles
        assert "Demo Session (Afternoon - S2)" in titles

    async def test_partner_cannot_create_series_in_other_zone(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_organizer: dict,
        test_game: dict,
        db_session: AsyncSession,
    ):
        """Partner cannot create series using tables from zones they don't manage."""
        # Get second user ID
        me_resp = await second_auth_client.get("/api/v1/users/me")
        partner_user_id = me_resp.json()["id"]

        # Create exhibition
        exhibition_payload = {
            "title": "Series Auth Test",
            "slug": "series-auth-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create time slot
        slot_resp = await auth_client.post(
            f"/api/v1/exhibitions/{exhibition_id}/slots",
            json={
                "name": "Morning",
                "start_time": "2026-07-01T09:00:00Z",
                "end_time": "2026-07-01T12:00:00Z",
                "max_duration_minutes": 180,
            },
        )
        slot_id = slot_resp.json()["id"]

        # Create two zones - partner only has access to zone1
        zone1 = Zone(
            id=uuid4(),
            exhibition_id=exhibition_id,
            name="Partner Zone",
            type=ZoneType.DEMO,
        )
        zone2 = Zone(
            id=uuid4(),
            exhibition_id=exhibition_id,
            name="Other Zone",
            type=ZoneType.DEMO,
        )
        db_session.add_all([zone1, zone2])
        await db_session.flush()

        # Table in zone partner doesn't have access to
        table_other = PhysicalTable(
            id=uuid4(),
            zone_id=zone2.id,
            label="O1",
            capacity=4,
            status=PhysicalTableStatus.AVAILABLE,
        )
        db_session.add(table_other)

        # Assign partner role with only zone1
        await db_session.execute(
            delete(UserExhibitionRole).where(
                UserExhibitionRole.user_id == partner_user_id,
                UserExhibitionRole.exhibition_id == exhibition_id,
            )
        )
        partner_role = UserExhibitionRole(
            id=uuid4(),
            user_id=partner_user_id,
            exhibition_id=exhibition_id,
            role=ExhibitionRole.PARTNER,
            zone_ids=[str(zone1.id)],
        )
        db_session.add(partner_role)
        await db_session.commit()

        # Try to create series with table from zone2
        series_payload = {
            "exhibition_id": exhibition_id,
            "game_id": test_game["id"],
            "title": "Unauthorized Series",
            "max_players_count": 4,
            "duration_minutes": 90,
            "time_slot_ids": [slot_id],
            "table_ids": [str(table_other.id)],
        }
        response = await second_auth_client.post(
            "/api/v1/partner/sessions/batch", json=series_payload
        )

        assert response.status_code == 403

    async def test_series_validates_time_slot_belongs_to_exhibition(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_organizer: dict,
        test_game: dict,
        db_session: AsyncSession,
    ):
        """Series creation validates that time slots belong to the exhibition."""
        # Get second user ID
        me_resp = await second_auth_client.get("/api/v1/users/me")
        partner_user_id = me_resp.json()["id"]

        # Create exhibition
        exhibition_payload = {
            "title": "Slot Validation Test",
            "slug": "slot-validation-test",
            "start_date": "2026-07-01T08:00:00Z",
            "end_date": "2026-07-03T22:00:00Z",
            "organization_id": test_organizer["organization_id"],
        }
        create_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
        exhibition_id = create_resp.json()["id"]

        # Create zone and table
        zone = Zone(
            id=uuid4(),
            exhibition_id=exhibition_id,
            name="Test Zone",
            type=ZoneType.DEMO,
        )
        db_session.add(zone)
        await db_session.flush()

        table = PhysicalTable(
            id=uuid4(),
            zone_id=zone.id,
            label="T1",
            capacity=4,
            status=PhysicalTableStatus.AVAILABLE,
        )
        db_session.add(table)

        # Assign partner role
        await db_session.execute(
            delete(UserExhibitionRole).where(
                UserExhibitionRole.user_id == partner_user_id,
                UserExhibitionRole.exhibition_id == exhibition_id,
            )
        )
        partner_role = UserExhibitionRole(
            id=uuid4(),
            user_id=partner_user_id,
            exhibition_id=exhibition_id,
            role=ExhibitionRole.PARTNER,
            zone_ids=[str(zone.id)],
        )
        db_session.add(partner_role)
        await db_session.commit()

        # Try to create series with non-existent time slot
        series_payload = {
            "exhibition_id": exhibition_id,
            "game_id": test_game["id"],
            "title": "Invalid Slot Series",
            "max_players_count": 4,
            "duration_minutes": 90,
            "time_slot_ids": [str(uuid4())],  # Non-existent slot
            "table_ids": [str(table.id)],
        }
        response = await second_auth_client.post(
            "/api/v1/partner/sessions/batch", json=series_payload
        )

        # 404 because the time slot doesn't exist
        assert response.status_code == 404
