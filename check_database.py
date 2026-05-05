"""
Check Database Connection and Tables
Verify database and tables exist for auto-scheduling
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'tazara_multi_route',
    'user': 'tazara',
    'password': 'tazara123'
}

def check_database():
    """Check database connection and tables"""
    try:
        print("Checking database connection...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        print("   Database connection successful!")
        
        # Check if tables exist
        print("Checking tables...")
        
        # Check schedules table
        cursor.execute("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name IN ('schedules', 'daily_assignments', 'customer_orders')
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"   Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['table_name']} ({table['table_type']})")
        
        # Check schedules table structure
        if any(t['table_name'] == 'schedules' for t in tables):
            print("Checking schedules table structure...")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'schedules'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            print("   Schedules table columns:")
            for col in columns:
                print(f"   - {col['column_name']} ({col['data_type']}) {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        
        # Check daily_assignments table structure
        if any(t['table_name'] == 'daily_assignments' for t in tables):
            print("Checking daily_assignments table structure...")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'daily_assignments'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            print("   Daily assignments table columns:")
            for col in columns:
                print(f"   - {col['column_name']} ({col['data_type']}) {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        
        # Check customer_orders table
        if any(t['table_name'] == 'customer_orders' for t in tables):
            print("Checking customer_orders table...")
            cursor.execute("SELECT COUNT(*) as count FROM customer_orders")
            result = cursor.fetchone()
            print(f"   Customer orders count: {result['count']}")
        
        cursor.close()
        conn.close()
        
        print("Database check completed successfully!")
        
    except Exception as e:
        print(f"Database check failed: {e}")
        print(f"Error Type: {type(e)}")
        print(f"Error Args: {e.args}")

if __name__ == "__main__":
    check_database()
