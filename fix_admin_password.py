"""
Fix Admin Password Hash
Update the admin user's password to use proper bcrypt hashing
"""

import psycopg2
from api.config import DB_CONFIG

def fix_admin_password():
    """Update admin password with proper bcrypt hash"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            # Create a proper bcrypt hash for "admin"
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed_password = pwd_context.hash("admin")
            
            print(f"Generated hash: {hashed_password}")
            
            # Update the admin user
            cur.execute("""
                UPDATE users 
                SET password_hash = %s 
                WHERE username = 'admin'
            """, (hashed_password,))
            
            conn.commit()
            print("✅ Admin password hash updated successfully")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error updating password: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_admin_password()
