import psycopg2
import os

def audit_tables():
    db_url = os.getenv('DATABASE_URL', 'postgresql://tazara:tazara123@localhost:5432/tazara_multi_route')
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        tables = [
            'train_operations', 'route_performance', 'daily_performance', 
            'performance_history', 'multi_route_audit_logs', 'schedule_comparisons'
        ]
        
        for table in tables:
            print(f"\n--- Audit for {table} ---")
            
            # Check column types
            cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
            """)
            print("  Columns:")
            for col, dtype in cursor.fetchall():
                print(f"    {col}: {dtype}")
                
            # Check constraints
            cursor.execute(f"""
                SELECT conname, pg_get_constraintdef(c.oid)
                FROM pg_constraint c
                JOIN pg_namespace n ON n.oid = c.connamespace
                WHERE conrelid = '{table}'::regclass;
            """)
            print("  Constraints:")
            for name, def_ in cursor.fetchall():
                print(f"    {name}: {def_}")
            
        conn.close()
    except Exception as e:
        print(f"Postgres error: {e}")

if __name__ == "__main__":
    audit_tables()
