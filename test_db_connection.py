"""
Test TAZARA Database Connection
"""

import psycopg2
import psycopg2.extras

def test_connection():
    """Test database connection with tazara user"""
    
    print("🔧 Testing TAZARA Database Connection")
    print("=" * 40)
    
    try:
        # Test connection
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="tazara",
            password="tazara123",
            database="tazara_multi_route"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL successfully!")
        
        # Test table access
        cursor.execute("SELECT COUNT(*) FROM multi_route_schedules")
        count = cursor.fetchone()[0]
        print(f"✅ multi_route_schedules table accessible (records: {count})")
        
        cursor.execute("SELECT COUNT(*) FROM system_configuration")
        config_count = cursor.fetchone()[0]
        print(f"✅ system_configuration table accessible (records: {config_count})")
        
        # Test insert
        cursor.execute("""
            INSERT INTO multi_route_schedules 
            (schedule_id, num_trains, total_days, cargo_requirements, 
             daily_actions, train_assignments, performance_metrics, 
             cost_breakdown_zmw, efficiency_analysis)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            'test_connection_' + str(int(time.time())),
            6,
            14,
            '{"DAR_KAPIRI": 500}',
            '[[0, 1, 2, 0, 0, 0]]',
            '[{"train_id": 0, "action": 0}]',
            '{"total_cargo_delivered": 500}',
            '{"net_profit_zmw": 50000}',
            '{"cargo_per_train": 83.3}'
        ))
        
        print("✅ Test insert successful")
        
        # Test select
        cursor.execute("SELECT schedule_id, num_trains FROM multi_route_schedules ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        print(f"✅ Test select successful: {result}")
        
        # Clean up
        cursor.execute("DELETE FROM multi_route_schedules WHERE schedule_id LIKE 'test_connection_%'")
        print("✅ Test data cleaned up")
        
        conn.close()
        
        print("\n🎉 Database connection test PASSED!")
        print("Your TAZARA database is ready for use.")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Make sure you ran the SQL script:")
        print("   psql -U postgres -f create_tazara_db.sql")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    import time
    test_connection()
