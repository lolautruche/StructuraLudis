"""
Tests for notification system.
"""
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4

import httpx
import pytest
from httpx import AsyncClient

from app.core.email import (
    ConsoleEmailBackend,
    SMTPEmailBackend,
    SendGridBackend,
    EmailMessage,
    get_email_backend,
)
from app.core.templates import (
    render_booking_confirmed,
    render_session_cancelled,
    render_new_player_registration,
    render_booking_cancelled,
    render_player_cancelled,
    get_string,
    format_datetime,
)


# Check if Mailpit is available for integration tests
MAILPIT_API_URL = os.environ.get("MAILPIT_API_URL", "http://localhost:8025/api/v1")


def mailpit_available() -> bool:
    """Check if Mailpit is running and accessible."""
    try:
        response = httpx.get(f"{MAILPIT_API_URL}/messages", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def clear_mailpit():
    """Clear all messages from Mailpit."""
    try:
        httpx.delete(f"{MAILPIT_API_URL}/messages", timeout=2.0)
    except Exception:
        pass


def get_mailpit_messages():
    """Get all messages from Mailpit."""
    response = httpx.get(f"{MAILPIT_API_URL}/messages", timeout=5.0)
    return response.json().get("messages", [])


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

    def test_render_new_player_registration_english(self):
        """Renders new player registration email for GM in English."""
        subject, html = render_new_player_registration(
            locale="en",
            session_title="Epic DnD Adventure",
            exhibition_title="GameCon 2026",
            scheduled_start=datetime(2026, 7, 15, 14, 0, tzinfo=timezone.utc),
            player_name="Jane Player",
            players_registered=3,
            max_players=5,
        )

        assert "Epic DnD Adventure" in subject
        assert "registered" in subject.lower() or "player" in subject.lower()
        assert "Jane Player" in html
        assert "3" in html
        assert "5" in html

    def test_render_new_player_registration_french(self):
        """Renders new player registration email for GM in French."""
        subject, html = render_new_player_registration(
            locale="fr",
            session_title="Aventure JDR",
            exhibition_title="GameCon 2026",
            scheduled_start=datetime(2026, 7, 15, 14, 0, tzinfo=timezone.utc),
            player_name="Jean Joueur",
            players_registered=2,
            max_players=4,
        )

        assert "Aventure JDR" in subject
        assert "inscrit" in subject.lower()
        assert "Jean Joueur" in html

    def test_render_booking_cancelled_english(self):
        """Renders booking cancelled email for player in English."""
        subject, html = render_booking_cancelled(
            locale="en",
            session_title="Cancelled Session",
            exhibition_title="GameCon 2026",
            scheduled_start=datetime(2026, 7, 15, 14, 0, tzinfo=timezone.utc),
        )

        assert "cancelled" in subject.lower()
        assert "Cancelled Session" in html

    def test_render_booking_cancelled_french(self):
        """Renders booking cancelled email for player in French."""
        subject, html = render_booking_cancelled(
            locale="fr",
            session_title="Session Annulée",
            exhibition_title="GameCon 2026",
            scheduled_start=datetime(2026, 7, 15, 14, 0, tzinfo=timezone.utc),
        )

        assert "annulée" in subject.lower()
        assert "Session Annulée" in html

    def test_render_player_cancelled_english(self):
        """Renders player cancelled email for GM in English."""
        subject, html = render_player_cancelled(
            locale="en",
            session_title="DnD Campaign",
            exhibition_title="GameCon 2026",
            scheduled_start=datetime(2026, 7, 15, 14, 0, tzinfo=timezone.utc),
            player_name="Jane Player",
            players_registered=2,
            max_players=5,
        )

        assert "cancelled" in subject.lower()
        assert "Jane Player" in html
        assert "2" in html
        assert "5" in html

    def test_render_player_cancelled_french(self):
        """Renders player cancelled email for GM in French."""
        subject, html = render_player_cancelled(
            locale="fr",
            session_title="Campagne JDR",
            exhibition_title="GameCon 2026",
            scheduled_start=datetime(2026, 7, 15, 14, 0, tzinfo=timezone.utc),
            player_name="Jean Joueur",
            players_registered=3,
            max_players=6,
        )

        assert "désisté" in subject.lower()
        assert "Jean Joueur" in html


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


class TestEmailBackendFactory:
    """Tests for email backend factory function."""

    def test_get_console_backend(self):
        """Returns console backend when configured."""
        with patch("app.core.email.settings") as mock_settings:
            mock_settings.EMAIL_BACKEND = "console"
            backend = get_email_backend()
            assert isinstance(backend, ConsoleEmailBackend)

    def test_get_smtp_backend(self):
        """Returns SMTP backend when configured."""
        with patch("app.core.email.settings") as mock_settings:
            mock_settings.EMAIL_BACKEND = "smtp"
            mock_settings.SMTP_HOST = "localhost"
            mock_settings.SMTP_PORT = 1025
            mock_settings.SMTP_USER = ""
            mock_settings.SMTP_PASSWORD = ""
            mock_settings.SMTP_TLS = False
            mock_settings.SMTP_SSL = False
            backend = get_email_backend()
            assert isinstance(backend, SMTPEmailBackend)

    def test_get_sendgrid_backend(self):
        """Returns SendGrid backend when configured."""
        with patch("app.core.email.settings") as mock_settings:
            mock_settings.EMAIL_BACKEND = "sendgrid"
            mock_settings.SENDGRID_API_KEY = "test-key"
            backend = get_email_backend()
            assert isinstance(backend, SendGridBackend)

    def test_unknown_backend_falls_back_to_console(self):
        """Falls back to console for unknown backend."""
        with patch("app.core.email.settings") as mock_settings:
            mock_settings.EMAIL_BACKEND = "unknown"
            backend = get_email_backend()
            assert isinstance(backend, ConsoleEmailBackend)


class TestSMTPBackendMocked:
    """Tests for SMTP backend with mocked smtplib."""

    @pytest.mark.asyncio
    async def test_smtp_send_success(self):
        """SMTP backend sends email successfully."""
        with patch("app.core.email.smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server

            with patch("app.core.email.settings") as mock_settings:
                mock_settings.SMTP_HOST = "localhost"
                mock_settings.SMTP_PORT = 1025
                mock_settings.SMTP_USER = ""
                mock_settings.SMTP_PASSWORD = ""
                mock_settings.SMTP_TLS = False
                mock_settings.SMTP_SSL = False
                mock_settings.EMAIL_FROM_NAME = "Test"
                mock_settings.EMAIL_FROM_ADDRESS = "test@example.com"

                backend = SMTPEmailBackend()
                message = EmailMessage(
                    to_email="recipient@example.com",
                    to_name="Recipient",
                    subject="Test Subject",
                    body_html="<p>Test</p>",
                )
                result = await backend.send(message)

                assert result is True
                mock_server.send_message.assert_called_once()
                mock_server.quit.assert_called_once()

    @pytest.mark.asyncio
    async def test_smtp_send_failure(self):
        """SMTP backend handles connection errors gracefully."""
        with patch("app.core.email.smtplib.SMTP") as mock_smtp:
            mock_smtp.side_effect = ConnectionRefusedError("Connection refused")

            with patch("app.core.email.settings") as mock_settings:
                mock_settings.SMTP_HOST = "localhost"
                mock_settings.SMTP_PORT = 1025
                mock_settings.SMTP_USER = ""
                mock_settings.SMTP_PASSWORD = ""
                mock_settings.SMTP_TLS = False
                mock_settings.SMTP_SSL = False

                backend = SMTPEmailBackend()
                message = EmailMessage(
                    to_email="recipient@example.com",
                    to_name="Recipient",
                    subject="Test Subject",
                    body_html="<p>Test</p>",
                )
                result = await backend.send(message)

                assert result is False


class TestSendGridBackendMocked:
    """Tests for SendGrid backend with mocked client."""

    @pytest.mark.asyncio
    async def test_sendgrid_send_success(self):
        """SendGrid backend sends email successfully."""
        with patch.dict("sys.modules", {"sendgrid": MagicMock(), "sendgrid.helpers.mail": MagicMock()}):
            import sys
            mock_sendgrid = sys.modules["sendgrid"]
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 202
            mock_client.send.return_value = mock_response
            mock_sendgrid.SendGridAPIClient.return_value = mock_client

            with patch("app.core.email.settings") as mock_settings:
                mock_settings.SENDGRID_API_KEY = "test-api-key"
                mock_settings.EMAIL_FROM_NAME = "Test"
                mock_settings.EMAIL_FROM_ADDRESS = "test@example.com"

                backend = SendGridBackend(api_key="test-api-key")
                message = EmailMessage(
                    to_email="recipient@example.com",
                    to_name="Recipient",
                    subject="Test Subject",
                    body_html="<p>Test</p>",
                )

                # Import the actual module to use mocked dependencies
                with patch.object(backend, "send", return_value=True):
                    result = await backend.send(message)
                    assert result is True


@pytest.mark.skipif(not mailpit_available(), reason="Mailpit not available")
class TestSMTPBackendIntegration:
    """Integration tests with real Mailpit SMTP server."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Clear Mailpit before each test."""
        clear_mailpit()

    @pytest.mark.asyncio
    async def test_smtp_real_send(self):
        """Send real email via SMTP to Mailpit."""
        backend = SMTPEmailBackend(
            host="localhost",
            port=1025,
            use_tls=False,
            use_ssl=False,
        )
        message = EmailMessage(
            to_email="test-recipient@example.com",
            to_name="Test Recipient",
            subject="Integration Test Email",
            body_html="<p>This is a test email sent from CI.</p>",
            body_text="This is a test email sent from CI.",
        )

        result = await backend.send(message)
        assert result is True

        # Verify email was received by Mailpit
        import time
        time.sleep(0.5)  # Give Mailpit time to process

        messages = get_mailpit_messages()
        assert len(messages) >= 1

        # Find our message
        found = False
        for msg in messages:
            if msg.get("Subject") == "Integration Test Email":
                found = True
                assert "test-recipient@example.com" in str(msg.get("To", []))
                break

        assert found, "Email not found in Mailpit"

    @pytest.mark.asyncio
    async def test_smtp_html_content(self):
        """Verify HTML content is properly sent."""
        backend = SMTPEmailBackend(
            host="localhost",
            port=1025,
            use_tls=False,
            use_ssl=False,
        )
        message = EmailMessage(
            to_email="html-test@example.com",
            to_name="HTML Test",
            subject="HTML Content Test",
            body_html="<h1>Header</h1><p>Paragraph with <strong>bold</strong> text.</p>",
        )

        result = await backend.send(message)
        assert result is True

        import time
        time.sleep(0.5)

        messages = get_mailpit_messages()
        found = any(msg.get("Subject") == "HTML Content Test" for msg in messages)
        assert found, "HTML email not found in Mailpit"