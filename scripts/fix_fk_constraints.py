import psycopg2
import os

def migrate():
    db_url = os.getenv('DATABASE_URL', 'postgresql://tazara:tazara123@localhost:5432/tazara_multi_route')
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Starting precision migration...")
        
        tables_to_fix = [
            ('performance_history', 'performance_history_schedule_id_fkey'),
            ('train_operations', 'train_operations_schedule_id_fkey'),
            ('route_performance', 'route_performance_schedule_id_fkey'),
            ('daily_performance', 'daily_performance_schedule_id_fkey'),
            ('multi_route_audit_logs', 'multi_route_audit_logs_schedule_id_fkey'),
            ('schedule_comparisons', 'schedule_comparisons_multi_route_schedule_id_fkey')
        ]
        
        for table, constraint in tables_to_fix:
            print(f"Fixing table: {table}")
            
            # Check if column is already integer
            cursor.execute(f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'schedule_id'")
            res = cursor.fetchone()
            if not res:
                # Handle schedule_comparisons case (diff column name)
                cursor.execute(f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'multi_route_schedule_id'")
                res = cursor.fetchone()
                col = 'multi_route_schedule_id'
            else:
                col = 'schedule_id'
                
            if res and res[0] == 'integer':
                print(f"  {table}.{col} is already integer. Checking constraint...")
            else:
                print(f"  Converting {table}.{col} to integer...")
                
                # Drop constraint
                try:
                    cursor.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint};")
                except Exception as e:
                    print(f"  Warning dropping constraint {constraint}: {e}")
                
                # Convert column
                # This is tricky because we need to map string IDs to integer IDs
                # But for now, if it's empty or failed, we can just clear it or try to map
                try:
                    # Try to map existing values
                    cursor.execute(f"""
                        ALTER TABLE {table} 
                        ALTER COLUMN {col} TYPE INTEGER 
                        USING (
                            SELECT s.id FROM multi_route_schedules s 
                            WHERE s.schedule_id = {table}.{col}
                            LIMIT 1
                        );
                    """)
                except Exception as e:
                    print(f"  Direct conversion failed, trying brute force (NULLing old references): {e}")
                    cursor.execute(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE INTEGER USING NULL;")

            # Add correct constraint
            try:
                cursor.execute(f"ALTER TABLE {table} ADD CONSTRAINT {constraint} FOREIGN KEY ({col}) REFERENCES multi_route_schedules(id);")
                print(f"  Successfully fixed {table}")
            except Exception as e:
                print(f"  Error adding constraint to {table}: {e}")

        conn.close()
        print("Precision migration complete.")
    except Exception as e:
        print(f"Postgres error: {e}")

if __name__ == "__main__":
    migrate()
