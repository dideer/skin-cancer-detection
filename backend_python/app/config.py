"""
app/config.py
=============
Configuration classes for DermisAI Flask backend.

Usage in create_app():
    app.config.from_object(config_by_name[env])

All sensitive values are read from environment variables (loaded
from .env by python-dotenv before this module is imported).
"""

import os
from datetime import timedelta


class Config:
    """Base configuration — shared defaults for all environments."""

    # ── Flask core ───────────────────────────────────────────
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "fallback-dev-secret")

    # ── Database ─────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres123@localhost:5432/skin_cancer_db",
    )
    # Disable modification tracking (saves memory, not needed with SQLAlchemy events)
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # ── JWT ──────────────────────────────────────────────────
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "fallback-jwt-secret")
    # Access tokens expire after 1 hour by default
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # ── CORS ─────────────────────────────────────────────────
    # Stored as a comma-separated string in .env; parsed into a list here.
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.environ.get(
            "CORS_ORIGINS",
            "http://localhost:5000,http://127.0.0.1:5000,http://localhost:5500,http://127.0.0.1:5500",
        ).split(",")
        if origin.strip()
    ]

    # ── File uploads ─────────────────────────────────────────
    MAX_CONTENT_LENGTH: int = 10 * 1024 * 1024  # 10 MB hard limit
    UPLOAD_FOLDER: str = os.path.join(os.path.dirname(__file__), "..", "uploads")
    ALLOWED_EXTENSIONS: set[str] = {"jpg", "jpeg", "png", "webp"}


class DevelopmentConfig(Config):
    """Development — verbose errors, auto-reload, no HTTPS enforcement."""

    DEBUG: bool = True
    TESTING: bool = False

    # Echo all SQL statements to the console for debugging
    SQLALCHEMY_ECHO: bool = True


class ProductionConfig(Config):
    """Production — strict security, no debug output."""

    DEBUG: bool = False
    TESTING: bool = False
    SQLALCHEMY_ECHO: bool = False

    # Enforce HTTPS cookies in production
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"


class TestingConfig(Config):
    """Testing — uses an in-memory SQLite DB, disables CSRF/JWT expiry."""

    DEBUG: bool = True
    TESTING: bool = True
    SQLALCHEMY_ECHO: bool = False

    # Use a fast in-memory database for unit tests
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"

    # Disable JWT expiry so tests don't need to manage token refresh
    JWT_ACCESS_TOKEN_EXPIRES: bool = False  # type: ignore[assignment]


# ── Registry ─────────────────────────────────────────────────────────────────
# Maps the FLASK_ENV value from .env to the matching config class.
config_by_name: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}

# Fallback if FLASK_ENV is not set or unrecognised
default_config = DevelopmentConfig
