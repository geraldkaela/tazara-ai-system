import sqlite3
import psycopg2
import os
from pathlib import Path

def check_sqlite():
    print("-" * 40)
    print("CHECKING SQLITE (database/tazara.db)")
    print("-" * 40)
    db_path = Path("database/tazara.db")
    if not db_path.exists():
        print(f"File not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Total tables: {len(tables)}")
        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  Table: {table_name} - Rows: {count}")
        conn.close()
    except Exception as e:
        print(f"SQLite error: {e}")

def check_postgres():
    print("\n" + "-" * 40)
    print("CHECKING POSTGRES (tazara_multi_route)")
    print("-" * 40)
    db_url = os.getenv('DATABASE_URL', 'postgresql://tazara:tazara123@localhost:5432/tazara_multi_route')
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print(f"Total tables: {len(tables)}")
        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  Table: {table_name} - Rows: {count}")
        conn.close()
    except Exception as e:
        print(f"Postgres error: {e}")

if __name__ == "__main__":
    check_sqlite()
    check_postgres()
