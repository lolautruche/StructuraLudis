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

    # Security (to be expanded later)
    SECRET_KEY: str = "change-me-in-production"


# Singleton instance
settings = Settings()