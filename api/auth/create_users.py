"""
Create sample users with different roles for RBAC testing
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib

def create_sample_users():
    """Create sample users with different roles"""
    
    conn = psycopg2.connect(
        host='localhost',
        database='tazara_multi_route',
        user='tazara',
        password='tazara123'
    )
    
    try:
        with conn.cursor() as cursor:
            # Sample users data
            users_data = [
                ('manager', 'manager@tazara.rail', 'manager123', 'manager', 'Schedule and user management'),
                ('operator', 'operator@tazara.rail', 'operator123', 'operator', 'Daily operations'),
                ('viewer', 'viewer@tazara.rail', 'viewer123', 'viewer', 'Read-only access'),
                ('supervisor', 'supervisor@tazara.rail', 'super123', 'manager', 'Senior management')
            ]
            
            for username, email, password, role, description in users_data:
                # Generate SHA-256 password hash
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                # Create user
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (username) DO UPDATE
                    SET email = EXCLUDED.email,
                        role = EXCLUDED.role,
                        updated_at = CURRENT_TIMESTAMP
                """, (username, email, password_hash, role))
                
                print(f"✅ Created/Updated user: {username} ({role})")
            
            conn.commit()
            print("\n🎉 Sample users created successfully!")
            print("\n📋 User Credentials:")
            print("┌─────────────┬──────────────────────┬─────────────┬──────────┐")
            print("│ Username    │ Email                 │ Role        │ Password │")
            print("├─────────────┼──────────────────────┼─────────────┼──────────┤")
            print("│ admin       │ admin@tazara.rail     │ admin       │ admin    │")
            print("│ manager     │ manager@tazara.rail   │ manager     │ manager123│")
            print("│ operator    │ operator@tazara.rail  │ operator    │ operator123│")
            print("│ viewer      │ viewer@tazara.rail    │ viewer      │ viewer123│")
            print("│ supervisor  │ supervisor@tazara.rail│ manager     │ super123 │")
            print("└─────────────┴──────────────────────┴─────────────┴──────────┘")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating sample users: {e}")
    finally:
        conn.close()

def show_user_permissions():
    """Show permissions for each user role"""
    from api.auth.rbac import RBACManager, Role
    
    print("\n🔐 Role Permissions Summary:")
    print("=" * 60)
    
    for role in Role:
        features = RBACManager.get_accessible_features(role.value)
        print(f"\n📋 {role.value.upper()} Role:")
        
        for category, permissions in features.items():
            if permissions:
                print(f"  {category.title()}: {', '.join(permissions)}")

if __name__ == "__main__":
    create_sample_users()
    show_user_permissions()
