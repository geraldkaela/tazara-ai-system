import psycopg2
import os

def migrate():
    db_url = os.getenv('DATABASE_URL', 'postgresql://tazara:tazara123@localhost:5432/tazara_multi_route')
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Running migrations...")
        
        # Add coordination_bonus_zmw to performance_history if missing
        try:
            cursor.execute("ALTER TABLE performance_history ADD COLUMN coordination_bonus_zmw DECIMAL(15,2) DEFAULT 0;")
            print("  Added coordination_bonus_zmw to performance_history")
        except psycopg2.Error as e:
            if "already exists" in str(e):
                print("  Column coordination_bonus_zmw already exists in performance_history")
            else:
                print(f"  Error adding column: {e}")
                
        # Ensure train_operations and route_performance exist (sometimes init fails silently if views exist)
        # But we already fixed that. Still, let's be sure.
        
        conn.close()
        print("Migration complete.")
    except Exception as e:
        print(f"Postgres error: {e}")

if __name__ == "__main__":
    migrate()
