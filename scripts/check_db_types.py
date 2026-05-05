import psycopg2
import os

def check_types():
    db_url = os.getenv('DATABASE_URL', 'postgresql://tazara:tazara123@localhost:5432/tazara_multi_route')
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        print("Checking multi_route_schedules columns:")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'multi_route_schedules'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        for col_name, data_type in columns:
            print(f"  {col_name}: {data_type}")
            
        conn.close()
    except Exception as e:
        print(f"Postgres error: {e}")

if __name__ == "__main__":
    check_types()
