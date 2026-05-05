"""
Debug Authentication Issues
Check database connection and user data
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from api.config import DB_CONFIG

def debug_auth():
    """Debug authentication setup"""
    print("🔍 Debugging TAZARA Authentication System")
    print("=" * 50)
    
    try:
        # Test database connection
        print("\n1. Testing database connection...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connection successful")
        
        # Check users table
        print("\n2. Checking users table...")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()
            print(f"✅ Found {len(users)} users in database")
            
            for user in users:
                print(f"   User: {user['username']}, Role: {user['role']}, Active: {user['is_active']}")
        
        # Test simple password verification
        print("\n3. Testing password verification...")
        from api.auth.auth import authenticate_user
        user = authenticate_user("admin", "admin")
        if user:
            print(f"✅ Authentication successful for user: {user.username}")
        else:
            print("❌ Authentication failed")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_auth()
