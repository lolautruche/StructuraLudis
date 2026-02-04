"""
Tests for User API endpoints (JS.B6 - Agenda Management).
"""
import pytest
from typing import AsyncGenerator
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
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
async def test_exhibition_with_slot(
    auth_client: AsyncClient,
    test_organizer: dict,
    second_organizer: dict,
    db_session,
) -> dict:
    """Create an exhibition with a zone and time slot (#105 - time slots at zone level).

    Both test_organizer and second_organizer get ORGANIZER roles for the exhibition.
    """
    from uuid import uuid4
    from app.domain.user.entity import UserExhibitionRole
    from app.domain.shared.entity import ExhibitionRole

    exhibition_payload = {
        "title": "User Test Convention",
        "slug": "user-test-convention",
        "start_date": "2026-07-01T08:00:00Z",
        "end_date": "2026-07-03T22:00:00Z",
        "organization_id": test_organizer["organization_id"],
    }
    exhibition_resp = await auth_client.post("/api/v1/exhibitions/", json=exhibition_payload)
    exhibition_id = exhibition_resp.json()["id"]

    # Add second_organizer as ORGANIZER for this exhibition (#99)
    second_organizer_role = UserExhibitionRole(
        id=uuid4(),
        user_id=second_organizer["id"],
        exhibition_id=exhibition_id,
        role=ExhibitionRole.ORGANIZER,
    )
    db_session.add(second_organizer_role)
    await db_session.commit()

    # Create zone first (#105 - time slots are now at zone level)
    zone_payload = {"name": "Main Hall", "exhibition_id": exhibition_id}
    zone_resp = await auth_client.post("/api/v1/zones/", json=zone_payload)
    zone_id = zone_resp.json()["id"]

    # Create time slot on the zone
    slot_payload = {
        "name": "Afternoon",
        "start_time": "2026-07-01T14:00:00Z",
        "end_time": "2026-07-01T18:00:00Z",
        "max_duration_minutes": 240,
        "buffer_time_minutes": 15,
    }
    slot_resp = await auth_client.post(
        f"/api/v1/zones/{zone_id}/slots", json=slot_payload
    )

    return {
        "exhibition_id": exhibition_id,
        "zone_id": zone_id,
        "time_slot_id": slot_resp.json()["id"],
    }


class TestUserProfile:
    """Tests for user profile endpoints."""

    async def test_get_current_user(self, auth_client: AsyncClient):
        """Get current user returns profile."""
        response = await auth_client.get("/api/v1/users/me")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Get current user without auth returns 401."""
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401

    async def test_update_profile(self, auth_client: AsyncClient):
        """Update current user profile."""
        response = await auth_client.put(
            "/api/v1/users/me",
            json={"full_name": "Updated Name", "locale": "fr"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["locale"] == "fr"

    async def test_update_profile_with_birth_date(self, auth_client: AsyncClient):
        """Update profile including birth_date."""
        response = await auth_client.put(
            "/api/v1/users/me",
            json={"birth_date": "1990-05-15"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["birth_date"] == "1990-05-15"


class TestPasswordChange:
    """Tests for password change endpoint."""

    @pytest.fixture
    async def user_with_password(self, db_session) -> dict:
        """Create a test user with a known hashed password."""
        from app.core.security import get_password_hash
        from app.domain.user.entity import User
        from app.domain.shared.entity import GlobalRole
        from uuid import uuid4

        user = User(
            id=uuid4(),
            email="pwdtest@example.com",
            hashed_password=get_password_hash("testpassword"),
            full_name="Test User",
            global_role=GlobalRole.USER,
            is_active=True,
            email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        return {
            "id": str(user.id),
            "email": user.email,
            "password": "testpassword",
        }

    @pytest.fixture
    async def password_auth_client(
        self,
        db_session,
        user_with_password: dict,
    ) -> AsyncGenerator[AsyncClient, None]:
        """Create authenticated client for user with known password."""
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        from app.core.database import get_db

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-ID": user_with_password["id"]},
        ) as ac:
            yield ac

        app.dependency_overrides.clear()

    async def test_change_password_success(
        self,
        password_auth_client: AsyncClient,
        user_with_password: dict,
        db_session,
    ):
        """Change password with correct current password."""
        response = await password_auth_client.put(
            "/api/v1/users/me/password",
            json={
                "current_password": user_with_password["password"],
                "new_password": "newpassword123",
            },
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"

        # Verify password was actually changed by checking the hash
        from sqlalchemy import select
        from app.domain.user.entity import User
        from app.core.security import verify_password

        result = await db_session.execute(
            select(User).where(User.email == user_with_password["email"])
        )
        user = result.scalar_one()
        assert verify_password("newpassword123", user.hashed_password)

    async def test_change_password_wrong_current(
        self,
        password_auth_client: AsyncClient,
    ):
        """Change password with wrong current password fails."""
        response = await password_auth_client.put(
            "/api/v1/users/me/password",
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123",
            },
        )

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    async def test_change_password_too_short(
        self,
        password_auth_client: AsyncClient,
        user_with_password: dict,
    ):
        """Change password with too short new password fails."""
        response = await password_auth_client.put(
            "/api/v1/users/me/password",
            json={
                "current_password": user_with_password["password"],
                "new_password": "short",
            },
        )

        assert response.status_code == 422


class TestMySessionsList:
    """Tests for listing user's sessions (as GM)."""

    async def test_list_my_sessions_empty(
        self,
        auth_client: AsyncClient,
    ):
        """List returns empty when no sessions."""
        response = await auth_client.get("/api/v1/users/me/sessions")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_my_sessions(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """List returns sessions created by user."""
        # Create a session
        payload = {
            "title": "My GM Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 5,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        await auth_client.post("/api/v1/sessions/", json=payload)

        response = await auth_client.get("/api/v1/users/me/sessions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "My GM Session"
        assert "exhibition_title" in data[0]
        assert "confirmed_players" in data[0]
        assert "waitlist_count" in data[0]

    async def test_list_my_sessions_filter_exhibition(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """List can filter by exhibition."""
        # Create a session
        payload = {
            "title": "Filtered Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 5,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T17:00:00Z",
        }
        await auth_client.post("/api/v1/sessions/", json=payload)

        # Filter by correct exhibition
        response = await auth_client.get(
            "/api/v1/users/me/sessions",
            params={"exhibition_id": test_exhibition_with_slot["exhibition_id"]},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Filter by wrong exhibition
        response2 = await auth_client.get(
            "/api/v1/users/me/sessions",
            params={"exhibition_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert response2.status_code == 200
        assert len(response2.json()) == 0


class TestMyBookingsList:
    """Tests for listing user's bookings (as player)."""

    async def _create_validated_session(
        self,
        auth_client: AsyncClient,
        exhibition_id: str,
        time_slot_id: str,
        game_id: str,
    ) -> str:
        """Helper to create a validated session."""
        payload = {
            "title": "Bookable Session",
            "exhibition_id": exhibition_id,
            "time_slot_id": time_slot_id,
            "game_id": game_id,
            "max_players_count": 5,
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

    async def test_list_my_bookings_empty(
        self,
        auth_client: AsyncClient,
    ):
        """List returns empty when no bookings."""
        response = await auth_client.get("/api/v1/users/me/bookings")

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_my_bookings(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """List returns bookings for user."""
        session_id = await self._create_validated_session(
            auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
        )

        # Book the session
        await auth_client.post(
            f"/api/v1/sessions/{session_id}/bookings",
            json={"role": "PLAYER"},
        )

        response = await auth_client.get("/api/v1/users/me/bookings")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["session_title"] == "Bookable Session"
        assert "exhibition_title" in data[0]
        assert "gm_name" in data[0]


class TestUserAgenda:
    """Tests for user agenda endpoint (JS.B6)."""

    async def _create_validated_session(
        self,
        auth_client: AsyncClient,
        exhibition_id: str,
        time_slot_id: str,
        game_id: str,
        title: str,
        start: str,
        end: str,
    ) -> str:
        """Helper to create a validated session."""
        payload = {
            "title": title,
            "exhibition_id": exhibition_id,
            "time_slot_id": time_slot_id,
            "game_id": game_id,
            "max_players_count": 5,
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

    async def test_get_agenda(
        self,
        auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Get agenda returns sessions and bookings."""
        # Create a session as GM
        payload = {
            "title": "My GM Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 5,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T15:00:00Z",
        }
        await auth_client.post("/api/v1/sessions/", json=payload)

        response = await auth_client.get(
            f"/api/v1/users/me/agenda/{test_exhibition_with_slot['exhibition_id']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exhibition_title"] == "User Test Convention"
        assert len(data["my_sessions"]) == 1
        assert data["my_sessions"][0]["title"] == "My GM Session"
        assert "conflicts" in data

    async def test_agenda_exhibition_not_found(
        self,
        auth_client: AsyncClient,
    ):
        """Agenda for non-existent exhibition returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await auth_client.get(f"/api/v1/users/me/agenda/{fake_id}")

        assert response.status_code == 404

    async def test_agenda_detects_conflicts(
        self,
        auth_client: AsyncClient,
        second_auth_client: AsyncClient,
        test_exhibition_with_slot: dict,
        test_game: dict,
    ):
        """Agenda detects overlapping schedules."""
        # Create a session as GM (14:00-15:30)
        gm_session = {
            "title": "GM Session",
            "exhibition_id": test_exhibition_with_slot["exhibition_id"],
            "time_slot_id": test_exhibition_with_slot["time_slot_id"],
            "game_id": test_game["id"],
            "max_players_count": 5,
            "scheduled_start": "2026-07-01T14:00:00Z",
            "scheduled_end": "2026-07-01T15:30:00Z",
        }
        await auth_client.post("/api/v1/sessions/", json=gm_session)

        # Create another session by different GM (15:00-17:00)
        player_session_id = await self._create_validated_session(
            second_auth_client,
            test_exhibition_with_slot["exhibition_id"],
            test_exhibition_with_slot["time_slot_id"],
            test_game["id"],
            "Player Session",
            "2026-07-01T15:00:00Z",
            "2026-07-01T17:00:00Z",
        )

        # Book as player (this overlaps with GM session)
        await auth_client.post(
            f"/api/v1/sessions/{player_session_id}/bookings",
            json={"role": "PLAYER"},
        )

        # Get agenda - should show conflict
        response = await auth_client.get(
            f"/api/v1/users/me/agenda/{test_exhibition_with_slot['exhibition_id']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["my_sessions"]) == 1
        assert len(data["my_bookings"]) == 1
        assert len(data["conflicts"]) > 0
        # Conflicts are now structured objects
        conflict = data["conflicts"][0]
        assert "session1_title" in conflict
        assert "session1_role" in conflict
        assert "session2_title" in conflict
        assert "session2_role" in conflict


class TestMyExhibitions:
    """Tests for My Exhibitions endpoint (Issue #96 - JS.C11)."""

    async def test_my_exhibitions_empty(
        self,
        auth_client: AsyncClient,
    ):
        """Returns empty lists when user has no exhibitions."""
        response = await auth_client.get("/api/v1/users/me/exhibitions")

        assert response.status_code == 200
        data = response.json()
        assert data["organized"] == []
        assert data["registered"] == []

    async def test_my_exhibitions_with_organized_and_registered(
        self,
        auth_client: AsyncClient,
        test_organizer: dict,
        db_session,
    ):
        """Returns both organized and registered exhibitions correctly."""
        from app.domain.exhibition.entity import Exhibition, ExhibitionRegistration
        from app.domain.organization.entity import Organization
        from app.domain.user.entity import UserExhibitionRole
        from app.domain.shared.entity import ExhibitionStatus, ExhibitionRole
        from datetime import datetime, timezone

        user_id = auth_client.headers.get("X-User-ID")

        # Create organization
        org = Organization(id=uuid4(), name="Test Org", slug="test-org-myex")
        db_session.add(org)

        # Create exhibition user organizes (PUBLISHED)
        organized_exhibition = Exhibition(
            id=uuid4(),
            organization_id=org.id,
            created_by_id=user_id,
            title="My Organized Event",
            slug="my-organized-event",
            start_date=datetime(2026, 8, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 8, 3, tzinfo=timezone.utc),
            status=ExhibitionStatus.PUBLISHED,
        )
        db_session.add(organized_exhibition)

        # Assign organizer role
        org_role = UserExhibitionRole(
            id=uuid4(),
            user_id=user_id,
            exhibition_id=organized_exhibition.id,
            role=ExhibitionRole.ORGANIZER,
        )
        db_session.add(org_role)

        # Create another exhibition user is only registered to (PUBLISHED)
        registered_exhibition = Exhibition(
            id=uuid4(),
            organization_id=org.id,
            created_by_id=user_id,  # Use same user as creator for FK
            title="Event I Attend",
            slug="event-i-attend",
            start_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 9, 3, tzinfo=timezone.utc),
            status=ExhibitionStatus.PUBLISHED,
        )
        db_session.add(registered_exhibition)

        # Register to the second exhibition (no role)
        registration = ExhibitionRegistration(
            id=uuid4(),
            user_id=user_id,
            exhibition_id=registered_exhibition.id,
        )
        db_session.add(registration)
        await db_session.commit()

        response = await auth_client.get("/api/v1/users/me/exhibitions")

        assert response.status_code == 200
        data = response.json()

        # Should have 1 organized and 1 registered
        assert len(data["organized"]) == 1
        assert data["organized"][0]["id"] == str(organized_exhibition.id)
        assert data["organized"][0]["can_manage"] is True

        assert len(data["registered"]) == 1
        assert data["registered"][0]["id"] == str(registered_exhibition.id)
        assert data["registered"][0]["is_user_registered"] is True
        assert data["registered"][0]["can_manage"] is False

    async def test_my_exhibitions_organizer_not_duplicated(
        self,
        auth_client: AsyncClient,
        test_organizer: dict,
        db_session,
    ):
        """Organizer should not appear in registered list even if also registered."""
        from app.domain.exhibition.entity import Exhibition, ExhibitionRegistration
        from app.domain.organization.entity import Organization
        from app.domain.user.entity import UserExhibitionRole
        from app.domain.shared.entity import ExhibitionStatus, ExhibitionRole
        from datetime import datetime, timezone

        user_id = auth_client.headers.get("X-User-ID")

        # Create organization
        org = Organization(id=uuid4(), name="Dup Org", slug="dup-org")
        db_session.add(org)

        # Create exhibition
        exhibition = Exhibition(
            id=uuid4(),
            organization_id=org.id,
            created_by_id=user_id,
            title="Dup Test Event",
            slug="dup-test-event",
            start_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 10, 3, tzinfo=timezone.utc),
            status=ExhibitionStatus.PUBLISHED,
        )
        db_session.add(exhibition)

        # Assign organizer role
        org_role = UserExhibitionRole(
            id=uuid4(),
            user_id=user_id,
            exhibition_id=exhibition.id,
            role=ExhibitionRole.ORGANIZER,
        )
        db_session.add(org_role)

        # ALSO register (should not appear twice)
        registration = ExhibitionRegistration(
            id=uuid4(),
            user_id=user_id,
            exhibition_id=exhibition.id,
        )
        db_session.add(registration)
        await db_session.commit()

        response = await auth_client.get("/api/v1/users/me/exhibitions")

        assert response.status_code == 200
        data = response.json()

        # Should appear in organized only (not duplicated in registered)
        assert len(data["organized"]) == 1
        assert data["registered"] == []
