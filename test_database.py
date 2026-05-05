"""
Simple test to check if we have database connection
"""

import psycopg2

def test_database_connection():
    """Test if we can connect to the database"""
    print("🔍 TESTING DATABASE CONNECTION")
    print("=" * 50)
    
    try:
        # Try to connect to database
        conn = psycopg2.connect(
            host="localhost",
            database="tazara_multi_route",
            user="tazara",
            password="tazara123"
        )
        cursor = conn.cursor()
        
        print("✅ Database connection successful!")
        
        # Check if schedules table exists and has data
        cursor.execute("""
            SELECT COUNT(*) FROM multi_route_schedules
            WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
        """)
        
        count = cursor.fetchone()[0]
        print(f"📊 Schedules in last 30 days: {count}")
        
        if count > 0:
            print("🎯 DATA SOURCE: Real database data available")
        else:
            print("🎯 DATA SOURCE: No recent schedules (using sample data)")
        
        cursor.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("🎯 DATA SOURCE: Sample data (database not accessible)")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🎯 DATA SOURCE: Sample data (error occurred)")

if __name__ == "__main__":
    test_database_connection()
