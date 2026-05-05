import psycopg2
import os

def check_structure():
    db_url = os.getenv('DATABASE_URL', 'postgresql://tazara:tazara123@localhost:5432/tazara_multi_route')
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("--- multi_route_schedules columns ---")
        cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'multi_route_schedules'")
        for row in cursor.fetchall(): print(f"  {row[0]}: {row[1]}")
        
        print("\n--- multi_route_schedules data (sample) ---")
        cursor.execute("SELECT id, schedule_id FROM multi_route_schedules LIMIT 5")
        for row in cursor.fetchall(): print(f"  id={row[0]}, schedule_id={row[1]}")
        
        print("\n--- performance_history columns ---")
        cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'performance_history'")
        for row in cursor.fetchall(): print(f"  {row[0]}: {row[1]}")
        
        print("\n--- performance_history constraints ---")
        cursor.execute("""
            SELECT conname, pg_get_constraintdef(c.oid)
            FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE conrelid = 'performance_history'::regclass;
        """)
        for row in cursor.fetchall(): print(f"  {row[0]}: {row[1]}")
            
        conn.close()
    except Exception as e:
        print(f"Postgres error: {e}")

if __name__ == "__main__":
    check_structure()
