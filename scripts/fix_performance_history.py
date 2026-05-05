import psycopg2
import os

def fix_performance_history():
    db_url = os.getenv('DATABASE_URL', 'postgresql://tazara:tazara123@localhost:5432/tazara_multi_route')
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Fixing performance_history table...")
        
        # 1. Drop existing constraint
        try:
            cursor.execute("ALTER TABLE performance_history DROP CONSTRAINT IF EXISTS performance_history_schedule_id_fkey;")
            print("  Dropped existing constraint")
        except Exception as e:
            print(f"  Error dropping constraint: {e}")
            
        # 2. Convert schedule_id to integer
        # We'll map existing string values to their integer counterparts first
        try:
            print("  Mapping string schedule_ids to integers...")
            # We add a temporary column for the integer mapping
            cursor.execute("ALTER TABLE performance_history ADD COLUMN temp_id INTEGER;")
            cursor.execute("""
                UPDATE performance_history ph
                SET temp_id = s.id
                FROM multi_route_schedules s
                WHERE ph.schedule_id = s.schedule_id;
            """)
            
            # Now replace the old column
            cursor.execute("ALTER TABLE performance_history DROP COLUMN schedule_id;")
            cursor.execute("ALTER TABLE performance_history RENAME COLUMN temp_id TO schedule_id;")
            print("  Converted schedule_id to integer successfully")
        except Exception as e:
            print(f"  Mapping failed, attempting direct alter (NULLing references): {e}")
            # If mapping fails (e.g. no column), we just try to alter it
            cursor.execute("ALTER TABLE performance_history ALTER COLUMN schedule_id TYPE INTEGER USING NULL;")
            
        # 3. Add correct constraint
        try:
            cursor.execute("ALTER TABLE performance_history ADD CONSTRAINT performance_history_schedule_id_fkey FOREIGN KEY (schedule_id) REFERENCES multi_route_schedules(id);")
            print("  Added correct foreign key constraint")
        except Exception as e:
            print(f"  Error adding constraint: {e}")

        conn.close()
        print("Fix complete.")
    except Exception as e:
        print(f"Postgres error: {e}")

if __name__ == "__main__":
    fix_performance_history()
