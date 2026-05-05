import psycopg2
import os

def final_cleanup():
    db_url = os.getenv('DATABASE_URL', 'postgresql://tazara:tazara123@localhost:5432/tazara_multi_route')
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Cleaning up performance_history...")
        
        # 1. Take care of temp_id
        try:
            cursor.execute("ALTER TABLE performance_history DROP COLUMN IF EXISTS temp_id;")
            print("  Dropped temp_id")
        except: pass
            
        # 2. Ensure schedule_id is INTEGER and has correct FK
        try:
            # Drop old constraint if any
            cursor.execute("ALTER TABLE performance_history DROP CONSTRAINT IF EXISTS performance_history_schedule_id_fkey;")
            # Ensure type is integer (should be already from audit, but just in case)
            cursor.execute("ALTER TABLE performance_history ALTER COLUMN schedule_id TYPE INTEGER USING schedule_id::integer;")
            # Re-add constraint
            cursor.execute("ALTER TABLE performance_history ADD CONSTRAINT performance_history_schedule_id_fkey FOREIGN KEY (schedule_id) REFERENCES multi_route_schedules(id);")
            print("  Ensured schedule_id is integer and FK is correctly linked to multi_route_schedules(id)")
        except Exception as e:
            print(f"  Error fixing schedule_id/FK: {e}")
            
        # 3. Check for any dangling data that might violate the FK
        print("  Checking for orphaned records...")
        cursor.execute("SELECT COUNT(*) FROM performance_history ph WHERE NOT EXISTS (SELECT 1 FROM multi_route_schedules s WHERE s.id = ph.schedule_id)")
        orphaned = cursor.fetchone()[0]
        if orphaned > 0:
            print(f"  Found {orphaned} orphaned records. Deleting them to maintain integrity...")
            cursor.execute("DELETE FROM performance_history ph WHERE NOT EXISTS (SELECT 1 FROM multi_route_schedules s WHERE s.id = ph.schedule_id)")

        conn.close()
        print("Cleanup complete.")
    except Exception as e:
        print(f"Postgres error: {e}")

if __name__ == "__main__":
    final_cleanup()
