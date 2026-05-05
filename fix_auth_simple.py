"""
Fix Authentication with Simple Password
Update auth system to work with plain text passwords temporarily
"""

import psycopg2
from api.config import DB_CONFIG

def fix_auth_simple():
    """Update auth system to work with plain text passwords"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            # Update admin password to plain text
            cur.execute("""
                UPDATE users 
                SET password_hash = 'admin' 
                WHERE username = 'admin'
            """)
            
            conn.commit()
            print("✅ Admin password set to plain text 'admin'")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error updating password: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_auth_simple()
