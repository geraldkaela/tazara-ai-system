import os
import psycopg2
import sqlite3
from api.config import DB_CONFIG

def get_db_connection():
    \"\"\"Get a database connection using the central configuration\"\"\"
    # Always use PostgreSQL in production
    try:
        # Check if running on Railway
        if 'RAILWAY_SERVICE_POSTGRES_URL' in os.environ:
            conn = psycopg2.connect(**DB_CONFIG)
        else:
            # Local development - try PostgreSQL first, fallback to SQLite
            try:
                conn = psycopg2.connect(**DB_CONFIG)
            except:
                db_path = os.getenv('DB_PATH', 'database/tazara.db')
                conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def get_db_cursor():
    \"\"\"Get a database cursor\"\"\"
    conn = get_db_connection()
    return conn, conn.cursor()
