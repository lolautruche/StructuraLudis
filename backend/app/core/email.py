"""
Email backend abstraction.

Supports multiple email backends: SMTP, Gmail API, Console (for testing).
"""
import logging
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Email message data."""
    to_email: str
    to_name: Optional[str]
    subject: str
    body_html: str
    body_text: Optional[str] = None
    reply_to: Optional[str] = None


class EmailBackend(ABC):
    """Abstract base class for email backends."""

    @abstractmethod
    async def send(self, message: EmailMessage) -> bool:
        """
        Send an email message.

        Args:
            message: The email message to send

        Returns:
            True if sent successfully, False otherwise
        """
        pass


class ConsoleEmailBackend(EmailBackend):
    """
    Console backend for testing - logs emails instead of sending.
    """

    async def send(self, message: EmailMessage) -> bool:
        logger.info(
            "\n" + "=" * 60 + "\n"
            "EMAIL (Console Backend)\n"
            "=" * 60 + "\n"
            f"To: {message.to_name} <{message.to_email}>\n"
            f"Subject: {message.subject}\n"
            f"Reply-To: {message.reply_to or 'N/A'}\n"
            "-" * 60 + "\n"
            f"{message.body_text or message.body_html}\n"
            "=" * 60
        )
        return True


class SMTPEmailBackend(EmailBackend):
    """
    SMTP backend for sending emails via SMTP server.

    Works with any SMTP server including Mailpit for development.
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        user: str = None,
        password: str = None,
        use_tls: bool = None,
        use_ssl: bool = None,
    ):
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.user = user or settings.SMTP_USER
        self.password = password or settings.SMTP_PASSWORD
        self.use_tls = use_tls if use_tls is not None else settings.SMTP_TLS
        self.use_ssl = use_ssl if use_ssl is not None else settings.SMTP_SSL

    async def send(self, message: EmailMessage) -> bool:
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
            msg["To"] = (
                f"{message.to_name} <{message.to_email}>"
                if message.to_name
                else message.to_email
            )
            if message.reply_to:
                msg["Reply-To"] = message.reply_to

            # Attach text and HTML parts
            if message.body_text:
                msg.attach(MIMEText(message.body_text, "plain", "utf-8"))
            msg.attach(MIMEText(message.body_html, "html", "utf-8"))

            # Connect and send
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.host, self.port)
            else:
                server = smtplib.SMTP(self.host, self.port)

            try:
                if self.use_tls and not self.use_ssl:
                    server.starttls()

                if self.user and self.password:
                    server.login(self.user, self.password)

                server.send_message(msg)
                logger.info(f"Email sent to {message.to_email}: {message.subject}")
                return True

            finally:
                server.quit()

        except Exception as e:
            logger.error(f"Failed to send email to {message.to_email}: {e}")
            return False


class GmailAPIBackend(EmailBackend):
    """
    Gmail API backend for sending emails via Google's Gmail API.

    Requires OAuth2 credentials from Google Cloud Console.
    See: https://developers.google.com/gmail/api/quickstart/python
    """

    def __init__(
        self,
        credentials_file: str = None,
        token_file: str = None,
    ):
        self.credentials_file = credentials_file or settings.GMAIL_CREDENTIALS_FILE
        self.token_file = token_file or settings.GMAIL_TOKEN_FILE
        self._service = None

    def _get_service(self):
        """Get or create Gmail API service."""
        if self._service:
            return self._service

        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError(
                "Gmail API backend requires google-api-python-client, "
                "google-auth-httplib2, and google-auth-oauthlib. "
                "Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            )

        SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
        creds = None

        # Load existing token
        if self.token_file:
            import os
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_file:
                    raise ValueError("GMAIL_CREDENTIALS_FILE not configured")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for next time
            if self.token_file:
                with open(self.token_file, "w") as token:
                    token.write(creds.to_json())

        self._service = build("gmail", "v1", credentials=creds)
        return self._service

    async def send(self, message: EmailMessage) -> bool:
        try:
            import base64
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM_ADDRESS}>"
            msg["To"] = (
                f"{message.to_name} <{message.to_email}>"
                if message.to_name
                else message.to_email
            )
            if message.reply_to:
                msg["Reply-To"] = message.reply_to

            if message.body_text:
                msg.attach(MIMEText(message.body_text, "plain", "utf-8"))
            msg.attach(MIMEText(message.body_html, "html", "utf-8"))

            # Encode and send
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            service = self._get_service()
            service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()

            logger.info(f"Email sent via Gmail API to {message.to_email}: {message.subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email via Gmail API to {message.to_email}: {e}")
            return False


class SendGridBackend(EmailBackend):
    """
    SendGrid backend for production email sending.

    Recommended for production use due to excellent deliverability.
    Requires: pip install sendgrid
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.SENDGRID_API_KEY

    async def send(self, message: EmailMessage) -> bool:
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, To, Content
        except ImportError:
            raise ImportError(
                "SendGrid backend requires sendgrid package. "
                "Install with: pip install sendgrid"
            )

        try:
            sg = SendGridAPIClient(self.api_key)

            from_email = Email(settings.EMAIL_FROM_ADDRESS, settings.EMAIL_FROM_NAME)
            to_email = To(message.to_email, message.to_name)

            mail = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=message.subject,
            )

            # Add content
            if message.body_text:
                mail.add_content(Content("text/plain", message.body_text))
            mail.add_content(Content("text/html", message.body_html))

            if message.reply_to:
                from sendgrid.helpers.mail import ReplyTo
                mail.reply_to = ReplyTo(message.reply_to)

            response = sg.send(mail)

            if response.status_code in (200, 201, 202):
                logger.info(f"Email sent via SendGrid to {message.to_email}: {message.subject}")
                return True
            else:
                logger.error(f"SendGrid returned status {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email via SendGrid to {message.to_email}: {e}")
            return False


def get_email_backend() -> EmailBackend:
    """
    Get the configured email backend.

    Returns:
        EmailBackend instance based on EMAIL_BACKEND setting
    """
    backend = settings.EMAIL_BACKEND.lower()

    if backend == "console":
        return ConsoleEmailBackend()
    elif backend == "smtp":
        return SMTPEmailBackend()
    elif backend == "gmail":
        return GmailAPIBackend()
    elif backend == "sendgrid":
        return SendGridBackend()
    else:
        logger.warning(f"Unknown email backend '{backend}', falling back to console")
        return ConsoleEmailBackend()
