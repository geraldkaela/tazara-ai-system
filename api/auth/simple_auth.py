"""
Simple Authentication Setup - Bypass bcrypt issues
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib

def create_simple_auth():
    """Create authentication tables with simple password hashing"""
    
    conn = psycopg2.connect(
        host='localhost',
        database='tazara_multi_route',
        user='tazara',
        password='tazara123'
    )
    
    try:
        with conn.cursor() as cursor:
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'operator' CHECK (role IN ('admin', 'manager', 'operator', 'viewer')),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create simple admin user with SHA-256 hash
            admin_password = "admin"
            password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role)
                VALUES ('admin', 'admin@tazara.rail', %s, 'admin')
                ON CONFLICT (username) DO NOTHING
            """, (password_hash,))
            
            conn.commit()
            print("✅ Simple authentication tables created successfully")
            print("🔑 Default admin user: username='admin', password='admin'")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating auth tables: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_simple_auth()
