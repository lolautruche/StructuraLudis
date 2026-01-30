"""
Tests for notification system.
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.core.email import ConsoleEmailBackend, EmailMessage
from app.core.templates import (
    render_booking_confirmed,
    render_session_cancelled,
    get_string,
    format_datetime,
)


class TestEmailBackend:
    """Tests for email backends."""

    @pytest.mark.asyncio
    async def test_console_backend_sends_successfully(self):
        """Console backend always returns True."""
        backend = ConsoleEmailBackend()
        message = EmailMessage(
            to_email="test@example.com",
            to_name="Test User",
            subject="Test Subject",
            body_html="<p>Test body</p>",
        )
        result = await backend.send(message)
        assert result is True


class TestEmailTemplates:
    """Tests for email template rendering."""

    def test_render_booking_confirmed_english(self):
        """Renders booking confirmation in English."""
        subject, html = render_booking_confirmed(
            locale="en",
            session_title="Epic DnD Adventure",
            exhibition_title="GameCon 2026",
            scheduled_start=datetime(2026, 7, 15, 14, 0, tzinfo=timezone.utc),
            gm_name="John the DM",
            location="Hall A",
        )

        assert "Epic DnD Adventure" in subject
        assert "confirmed" in subject.lower()
        assert "Epic DnD Adventure" in html
        assert "GameCon 2026" in html
        assert "John the DM" in html
        assert "Hall A" in html

    def test_render_booking_confirmed_french(self):
        """Renders booking confirmation in French."""
        subject, html = render_booking_confirmed(
            locale="fr",
            session_title="Aventure JDR",
            exhibition_title="GameCon 2026",
            scheduled_start=datetime(2026, 7, 15, 14, 0, tzinfo=timezone.utc),
        )

        assert "confirmée" in subject.lower()
        assert "Aventure JDR" in html

    def test_render_session_cancelled_with_reason(self):
        """Renders cancellation with reason."""
        subject, html = render_session_cancelled(
            locale="en",
            session_title="Cancelled Session",
            exhibition_title="GameCon 2026",
            scheduled_start=datetime(2026, 7, 15, 14, 0, tzinfo=timezone.utc),
            cancellation_reason="GM is ill",
        )

        assert "cancelled" in subject.lower()
        assert "GM is ill" in html

    def test_get_string_english(self):
        """Gets English string."""
        result = get_string("booking_confirmed_greeting", "en")
        assert "confirmed" in result.lower()

    def test_get_string_french(self):
        """Gets French string."""
        result = get_string("booking_confirmed_greeting", "fr")
        assert "confirmée" in result.lower()

    def test_get_string_with_format(self):
        """Gets string with format arguments."""
        result = get_string(
            "booking_confirmed_subject",
            "en",
            session_title="Test Session"
        )
        assert "Test Session" in result

    def test_get_string_fallback_to_english(self):
        """Falls back to English for unknown locale."""
        result = get_string("booking_confirmed_greeting", "de")
        assert "confirmed" in result.lower()

    def test_format_datetime_english(self):
        """Formats datetime for English."""
        dt = datetime(2026, 7, 15, 14, 30, tzinfo=timezone.utc)
        date_str, time_str = format_datetime(dt, "en")

        assert "July" in date_str
        assert "15" in date_str
        assert "2026" in date_str

    def test_format_datetime_french(self):
        """Formats datetime for French."""
        dt = datetime(2026, 7, 15, 14, 30, tzinfo=timezone.utc)
        date_str, time_str = format_datetime(dt, "fr")

        assert "15/07/2026" == date_str
        assert "14:30" == time_str


class TestNotificationAPI:
    """Tests for notification API endpoints."""

    async def test_list_notifications_empty(
        self,
        auth_client: AsyncClient,
    ):
        """Returns empty list when no notifications."""
        response = await auth_client.get("/api/v1/notifications/")

        assert response.status_code == 200
        data = response.json()
        assert data["notifications"] == []
        assert data["total"] == 0
        assert data["unread_count"] == 0

    async def test_get_unread_count(
        self,
        auth_client: AsyncClient,
    ):
        """Returns unread count."""
        response = await auth_client.get("/api/v1/notifications/unread-count")

        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data
        assert data["unread_count"] == 0

    async def test_mark_all_read_empty(
        self,
        auth_client: AsyncClient,
    ):
        """Mark all read when no notifications."""
        response = await auth_client.post("/api/v1/notifications/mark-all-read")

        assert response.status_code == 200
        data = response.json()
        assert data["updated_count"] == 0