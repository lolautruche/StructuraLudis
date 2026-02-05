"""
Tests for event request API (Issue #92).

Tests the self-service event creation workflow.
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.shared.entity import GlobalRole, EventRequestStatus


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> dict:
    """Create a test admin user."""
    from app.domain.user.entity import User

    user = User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password="hashed_test_password",
        full_name="Test Admin",
        global_role=GlobalRole.ADMIN,
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "global_role": str(user.global_role),
    }


@pytest.fixture
async def admin_auth_client(
    db_session: AsyncSession, test_admin: dict
):
    """Create an authenticated test HTTP client (as admin)."""
    from httpx import ASGITransport, AsyncClient
    from app.core.database import get_db
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-User-ID": test_admin["id"]},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def user_auth_client(
    db_session: AsyncSession, test_user: dict
):
    """Create an authenticated test HTTP client (as regular user)."""
    from httpx import ASGITransport, AsyncClient
    from app.core.database import get_db
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-User-ID": test_user["id"]},
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def valid_request_data() -> dict:
    """Valid event request data."""
    return {
        "event_title": "My Awesome Convention",
        "event_description": "A great gaming convention",
        "event_start_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "event_end_date": (datetime.now(timezone.utc) + timedelta(days=32)).isoformat(),
        "event_location_name": "Convention Center",
        "event_city": "Paris",
        "event_country_code": "FR",
        "event_region": "ile-de-france",
        "event_timezone": "Europe/Paris",
        "organization_name": "My Gaming Association",
        "organization_contact_email": "contact@mygaming.org",
        "requester_message": "We organize gaming events since 2020.",
    }


class TestCreateEventRequest:
    """Tests for POST /api/v1/event-requests/"""

    async def test_create_request_success(
        self, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """Verified user can create an event request."""
        response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["event_title"] == valid_request_data["event_title"]
        assert data["organization_name"] == valid_request_data["organization_name"]
        assert data["status"] == "PENDING"
        assert "event_slug" in data
        assert "organization_slug" in data

    async def test_create_request_auto_generates_slugs(
        self, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """Slugs are automatically generated from titles."""
        response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["event_slug"] == "my-awesome-convention"
        assert data["organization_slug"] == "my-gaming-association"

    async def test_create_request_validates_dates(
        self, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """Start date must be before end date."""
        valid_request_data["event_start_date"] = valid_request_data["event_end_date"]
        valid_request_data["event_end_date"] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

        response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )

        assert response.status_code == 422  # Validation error

    async def test_create_request_requires_auth(
        self, client: AsyncClient, valid_request_data: dict
    ):
        """Anonymous users cannot create requests."""
        response = await client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )

        assert response.status_code == 401

    async def test_create_request_requires_verified_email(
        self, db_session: AsyncSession, valid_request_data: dict
    ):
        """User with unverified email cannot create requests."""
        from app.domain.user.entity import User
        from httpx import ASGITransport, AsyncClient
        from app.core.database import get_db
        from app.main import app

        # Create unverified user
        user = User(
            id=uuid4(),
            email="unverified@example.com",
            hashed_password="hashed_test_password",
            full_name="Unverified User",
            global_role=GlobalRole.USER,
            is_active=True,
            email_verified=False,  # Not verified
        )
        db_session.add(user)
        await db_session.commit()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-ID": str(user.id)},
        ) as ac:
            response = await ac.post(
                "/api/v1/event-requests/",
                json=valid_request_data,
            )

        app.dependency_overrides.clear()

        assert response.status_code == 403

    async def test_create_request_prevents_duplicate_pending(
        self, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """User cannot create multiple pending requests."""
        # Create first request
        response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )
        assert response.status_code == 201

        # Try to create second request
        valid_request_data["event_title"] = "Another Convention"
        response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )

        assert response.status_code == 409
        assert "already have a pending" in response.json()["detail"]


class TestListMyRequests:
    """Tests for GET /api/v1/event-requests/my"""

    async def test_list_my_requests(
        self, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """User can list their own requests."""
        # Create a request
        await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )

        response = await user_auth_client.get("/api/v1/event-requests/my")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["event_title"] == valid_request_data["event_title"]


class TestAdminListRequests:
    """Tests for GET /api/v1/event-requests/ (admin)"""

    async def test_admin_list_requests(
        self, admin_auth_client: AsyncClient, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """Admin can list all requests."""
        # Create a request as user
        await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )

        response = await admin_auth_client.get("/api/v1/event-requests/")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["pending_count"] == 1
        assert len(data["items"]) == 1

    async def test_admin_list_filter_by_status(
        self, admin_auth_client: AsyncClient, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """Admin can filter requests by status."""
        # Create a request
        await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )

        # Filter by PENDING
        response = await admin_auth_client.get("/api/v1/event-requests/?status=PENDING")
        assert response.status_code == 200
        assert response.json()["total"] == 1

        # Filter by APPROVED (should be empty)
        response = await admin_auth_client.get("/api/v1/event-requests/?status=APPROVED")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    async def test_user_cannot_list_all_requests(
        self, user_auth_client: AsyncClient
    ):
        """Regular user cannot access admin list endpoint."""
        response = await user_auth_client.get("/api/v1/event-requests/")

        assert response.status_code == 403


class TestReviewRequest:
    """Tests for POST /api/v1/event-requests/{id}/review"""

    async def test_approve_request(
        self, admin_auth_client: AsyncClient, user_auth_client: AsyncClient, valid_request_data: dict, db_session: AsyncSession
    ):
        """Admin can approve a request, creating org and exhibition."""
        # Create a request
        create_response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )
        request_id = create_response.json()["id"]

        # Approve
        response = await admin_auth_client.post(
            f"/api/v1/event-requests/{request_id}/review",
            json={"action": "approve"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"
        assert data["created_exhibition_id"] is not None
        assert data["created_organization_id"] is not None

        # Verify exhibition was created
        from app.domain.exhibition.entity import Exhibition
        from sqlalchemy import select

        result = await db_session.execute(
            select(Exhibition).where(Exhibition.id == data["created_exhibition_id"])
        )
        exhibition = result.scalar_one_or_none()
        assert exhibition is not None
        assert exhibition.title == valid_request_data["event_title"]

    async def test_request_changes(
        self, admin_auth_client: AsyncClient, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """Admin can request changes."""
        # Create a request
        create_response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )
        request_id = create_response.json()["id"]

        # Request changes
        response = await admin_auth_client.post(
            f"/api/v1/event-requests/{request_id}/review",
            json={
                "action": "request_changes",
                "admin_comment": "Please add more details about your organization.",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CHANGES_REQUESTED"
        assert data["admin_comment"] == "Please add more details about your organization."

    async def test_reject_request(
        self, admin_auth_client: AsyncClient, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """Admin can reject a request."""
        # Create a request
        create_response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )
        request_id = create_response.json()["id"]

        # Reject
        response = await admin_auth_client.post(
            f"/api/v1/event-requests/{request_id}/review",
            json={
                "action": "reject",
                "admin_comment": "This event does not meet our guidelines.",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"
        assert data["admin_comment"] == "This event does not meet our guidelines."

    async def test_request_changes_requires_comment(
        self, admin_auth_client: AsyncClient, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """Request changes action requires admin_comment."""
        # Create a request
        create_response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )
        request_id = create_response.json()["id"]

        # Try to request changes without comment
        response = await admin_auth_client.post(
            f"/api/v1/event-requests/{request_id}/review",
            json={"action": "request_changes"},
        )

        assert response.status_code == 422  # Validation error

    async def test_user_cannot_review(
        self, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """Regular user cannot review requests."""
        # Create a request
        create_response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )
        request_id = create_response.json()["id"]

        # Try to approve
        response = await user_auth_client.post(
            f"/api/v1/event-requests/{request_id}/review",
            json={"action": "approve"},
        )

        assert response.status_code == 403


class TestUpdateAndResubmit:
    """Tests for PUT /api/v1/event-requests/{id} and POST /api/v1/event-requests/{id}/resubmit"""

    async def test_update_after_changes_requested(
        self, admin_auth_client: AsyncClient, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """User can update their request after changes are requested."""
        # Create a request
        create_response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )
        request_id = create_response.json()["id"]

        # Admin requests changes
        await admin_auth_client.post(
            f"/api/v1/event-requests/{request_id}/review",
            json={
                "action": "request_changes",
                "admin_comment": "Please update the description.",
            },
        )

        # User updates
        response = await user_auth_client.put(
            f"/api/v1/event-requests/{request_id}",
            json={"event_description": "Updated description with more details."},
        )

        assert response.status_code == 200
        assert response.json()["event_description"] == "Updated description with more details."

    async def test_cannot_update_pending_request(
        self, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """User cannot update a pending request (must be CHANGES_REQUESTED)."""
        # Create a request
        create_response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )
        request_id = create_response.json()["id"]

        # Try to update while PENDING
        response = await user_auth_client.put(
            f"/api/v1/event-requests/{request_id}",
            json={"event_description": "Trying to update."},
        )

        assert response.status_code == 400
        assert "CHANGES_REQUESTED" in response.json()["detail"]

    async def test_resubmit_after_changes(
        self, admin_auth_client: AsyncClient, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """User can resubmit their request after making changes."""
        # Create a request
        create_response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )
        request_id = create_response.json()["id"]

        # Admin requests changes
        await admin_auth_client.post(
            f"/api/v1/event-requests/{request_id}/review",
            json={
                "action": "request_changes",
                "admin_comment": "Please update the description.",
            },
        )

        # User resubmits
        response = await user_auth_client.post(
            f"/api/v1/event-requests/{request_id}/resubmit",
        )

        assert response.status_code == 200
        assert response.json()["status"] == "PENDING"


class TestGetRequest:
    """Tests for GET /api/v1/event-requests/{id}"""

    async def test_owner_can_view_own_request(
        self, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """Owner can view their own request."""
        # Create a request
        create_response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )
        request_id = create_response.json()["id"]

        response = await user_auth_client.get(f"/api/v1/event-requests/{request_id}")

        assert response.status_code == 200
        assert response.json()["id"] == request_id

    async def test_admin_can_view_any_request(
        self, admin_auth_client: AsyncClient, user_auth_client: AsyncClient, valid_request_data: dict
    ):
        """Admin can view any request."""
        # Create a request as user
        create_response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )
        request_id = create_response.json()["id"]

        response = await admin_auth_client.get(f"/api/v1/event-requests/{request_id}")

        assert response.status_code == 200
        assert response.json()["id"] == request_id

    async def test_other_user_cannot_view_request(
        self, user_auth_client: AsyncClient, valid_request_data: dict, db_session: AsyncSession
    ):
        """Other users cannot view someone else's request."""
        from app.domain.user.entity import User
        from httpx import ASGITransport, AsyncClient
        from app.core.database import get_db
        from app.main import app

        # Create a request as user
        create_response = await user_auth_client.post(
            "/api/v1/event-requests/",
            json=valid_request_data,
        )
        request_id = create_response.json()["id"]

        # Create another user
        other_user = User(
            id=uuid4(),
            email="other@example.com",
            hashed_password="hashed_test_password",
            full_name="Other User",
            global_role=GlobalRole.USER,
            is_active=True,
            email_verified=True,
        )
        db_session.add(other_user)
        await db_session.commit()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-ID": str(other_user.id)},
        ) as ac:
            response = await ac.get(f"/api/v1/event-requests/{request_id}")

        app.dependency_overrides.clear()

        assert response.status_code == 403
