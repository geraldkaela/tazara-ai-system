"""
Simple Authentication Database Setup
Create users and audit_log tables with minimal bcrypt configuration
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from api.config import DB_CONFIG

def create_auth_tables():
    """Create users and audit tables (idempotent — safe to run on every startup)."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            SERIAL PRIMARY KEY,
                    username      VARCHAR(50)  UNIQUE NOT NULL,
                    email         VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role          VARCHAR(20)  NOT NULL DEFAULT 'operator',
                    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
                    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id         SERIAL PRIMARY KEY,
                    user_id    INTEGER REFERENCES users(id),
                    action     VARCHAR(50)  NOT NULL,
                    resource   VARCHAR(100),
                    details    JSONB,
                    ip_address INET,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Default admin with simple password
            cur.execute("""
                INSERT INTO users (username, email, password_hash, role)
                VALUES ('admin', 'admin@tazara.rail', 'admin', 'admin')
                ON CONFLICT (username) DO NOTHING
            """)

        conn.commit()
        print("✅ Auth tables created / verified OK")
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to create auth tables: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_auth_tables()
