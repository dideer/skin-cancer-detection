"""
app/config.py
=============
Configuration classes for DermisAI Flask backend.

Supports three environments:
- development (localhost)
- production (Render)
- testing (unit tests)

All sensitive values are read from environment variables.
Environment variables are loaded from .env by python-dotenv.
"""

import os
from datetime import timedelta


class Config:
    """Base configuration — shared defaults for all environments."""

    # ── Flask Core ───────────────────────────────────────────
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-fallback-secret-key-change-in-production")
    
    # ── Flask Settings ───────────────────────────────────────
    DEBUG: bool = False
    TESTING: bool = False
    
    # ── Database ─────────────────────────────────────────────
    # Tries to read DATABASE_URL from environment (Render provides this)
    # Falls back to local PostgreSQL for development
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres123@localhost:5432/skin_cancer_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = False

    # ── JWT Authentication ──────────────────────────────────
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "dev-fallback-jwt-secret-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # ── CORS Configuration ──────────────────────────────────
    # Comma-separated origins from environment, parsed into list
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.environ.get(
            "CORS_ORIGINS",
            "http://localhost:5000,http://127.0.0.1:5000,http://localhost:5500,http://127.0.0.1:5500",
        ).split(",")
        if origin.strip()
    ]

    # ── File Uploads ────────────────────────────────────────
    MAX_CONTENT_LENGTH: int = 10 * 1024 * 1024  # 10 MB hard limit
    UPLOAD_FOLDER: str = os.path.join(os.path.dirname(__file__), "..", "uploads")
    ALLOWED_EXTENSIONS: set[str] = {"jpg", "jpeg", "png", "webp"}
    
    # ── Session Configuration ───────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"


class DevelopmentConfig(Config):
    """
    Development configuration — verbose errors, auto-reload, debugging enabled.
    
    Used when FLASK_ENV=development (localhost)
    """

    DEBUG: bool = True
    TESTING: bool = False
    
    # Log all SQL queries to console
    SQLALCHEMY_ECHO: bool = True
    
    # Don't enforce HTTPS cookies in development
    SESSION_COOKIE_SECURE: bool = False


class ProductionConfig(Config):
    """
    Production configuration — strict security, no debug output.
    
    Used when FLASK_ENV=production (Render)
    """

    DEBUG: bool = False
    TESTING: bool = False
    
    # Don't log SQL queries in production
    SQLALCHEMY_ECHO: bool = False
    
    # Enforce HTTPS cookies in production
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"


class TestingConfig(Config):
    """
    Testing configuration — uses in-memory SQLite database.
    
    Used when running unit tests
    """

    DEBUG: bool = True
    TESTING: bool = True
    
    # Use in-memory SQLite for fast tests
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    
    # Don't log SQL in tests
    SQLALCHEMY_ECHO: bool = False
    
    # Disable JWT expiry for testing
    JWT_ACCESS_TOKEN_EXPIRES: bool = False  # type: ignore[assignment]


# ── Config Registry ──────────────────────────────────────────────────────────
# Maps FLASK_ENV environment variable to config class

config_by_name: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}

# Default fallback if FLASK_ENV is not set
default_config = DevelopmentConfig