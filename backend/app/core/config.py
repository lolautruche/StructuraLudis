"""
Application configuration.

Uses pydantic-settings for type-safe environment variable parsing.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    For example: DATABASE_URL, DEBUG, etc.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    APP_NAME: str = "Structura Ludis"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://sl_admin:sl_password@localhost:5432/structura_ludis"

    # Security / JWT
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REMEMBER_ME_TOKEN_EXPIRE_DAYS: int = 30  # 30 days for "remember me"

    # Email configuration (#37)
    # Backend: "smtp", "gmail", "console" (for testing)
    EMAIL_BACKEND: str = "console"
    EMAIL_ENABLED: bool = False  # Set to True to actually send emails
    EMAIL_FROM_ADDRESS: str = "noreply@structuraludis.com"
    EMAIL_FROM_NAME: str = "Structura Ludis"

    # SMTP settings (for EMAIL_BACKEND=smtp)
    # Dev: use Mailpit at localhost:1025 (docker-compose service sl-mail)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025  # Mailpit default
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = False  # Mailpit doesn't need TLS
    SMTP_SSL: bool = False

    # Gmail API settings (for EMAIL_BACKEND=gmail)
    # Requires OAuth2 credentials from Google Cloud Console
    GMAIL_CREDENTIALS_FILE: str = ""  # Path to credentials.json
    GMAIL_TOKEN_FILE: str = ""  # Path to token.json (auto-generated)

    # SendGrid settings (for EMAIL_BACKEND=sendgrid) - Recommended for production
    SENDGRID_API_KEY: str = ""

    # Firebase Cloud Messaging for push notifications
    FIREBASE_CREDENTIALS_FILE: str = ""  # Path to Firebase service account JSON
    PUSH_NOTIFICATIONS_ENABLED: bool = False

    # Frontend URL for email links (Issue #73)
    FRONTEND_URL: str = "http://localhost:3000"


# Singleton instance
settings = Settings()