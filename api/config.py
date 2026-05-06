"""
Central database & application configuration.
"""

import os

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

# Check if running on Railway
railway_pg_url = os.environ.get('RAILWAY_SERVICE_POSTGRES_URL', '')

if railway_pg_url:
    # Running on Railway - use the PostgreSQL service
    # The URL is like: postgres-production-097cf.up.railway.app
    # We need to use the internal proxy for connection
    DB_CONFIG = {
        "host": "trolley.proxy.rlwy.net",
        "port": "48704",
        "user": "postgres",
        "password": "tSaCccFLweXbbXLOQiXDxRLhyljbGEZF",
        "database": "railway"
    }
else:
    # Running locally - use your original settings
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "tazara_multi_route"),
        "user": os.getenv("DB_USER", "tazara"),
        "password": os.getenv("DB_PASSWORD", "tazara123"),
    }

# For debugging
print(f"DB_CONFIG in use: host={DB_CONFIG['host']}, database={DB_CONFIG['database']}")

# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE-ME-IN-PRODUCTION")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("CORS_ORIGINS", "")
CORS_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]
if not CORS_ORIGINS:
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = APP_ENV != "production"