"""
Central database & application configuration.
All settings are read from environment variables with safe fallbacks.

Set these in a .env file (never commit .env file to version control):
    DB_HOST=localhost
    DB_NAME=tazara_multi_route
    DB_USER=tazara
    DB_PASSWORD=your_secure_password_here
    CORS_ORIGINS=https://yourdomain.com
    JWT_SECRET_KEY=a-long-random-secret-change-this
"""

import os

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "database": os.getenv("DB_NAME",     "tazara_multi_route"),
    "user":     os.getenv("DB_USER",     "tazara"),
    "password": os.getenv("DB_PASSWORD", "tazara123"),
}

# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "CHANGE-ME-IN-PRODUCTION")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours (1440 minutes)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("CORS_ORIGINS", "")
CORS_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]
if not CORS_ORIGINS:
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG   = APP_ENV != "production"
