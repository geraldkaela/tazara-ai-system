"""Verify consolidated database contents."""
import sqlite3
from pathlib import Path

DB_PATH = Path("database/tazara.db")

def check_database():
    """Check all tables in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("DATABASE VERIFICATION: database/tazara.db")
    print("="*80)
    
    # Get all tables
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    tables = cursor.fetchall()
    
    print(f"\n📊 TOTAL TABLES: {len(tables)}\n")
    
    for (table_name,) in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        
        print(f"✅ {table_name}")
        print(f"   Records: {count}")
        print(f"   Columns: {', '.join(col_names)}")
        
        # Sample data for small tables
        if count > 0 and count <= 5:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            for row in rows:
                print(f"   → {row}")
        elif count > 5:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
            rows = cursor.fetchall()
            for row in rows:
                print(f"   → {row}")
            print(f"   ... ({count - 2} more records)")
        
        print()
    
    # Summary counts
    print("="*80)
    print("SUMMARY: Phase 2 Data Ingestion")
    print("="*80)
    
    phase2_tables = {
        "forecasting_models": "Model registry",
        "forecasts": "Demand forecasts",
        "risk_analysis": "Daily risk scores",
        "schedule_fragility": "Daily fragility scores",
        "bottleneck_periods": "Bottleneck periods",
        "backtest_results": "Validation windows",
        "what_if_scenarios": "What-if scenarios"
    }
    
    for table, desc in phase2_tables.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✅ {table:30s} ({desc:25s}): {count:4d} records")
        except sqlite3.OperationalError:
            print(f"  ❌ {table:30s} NOT FOUND")
    
    print("\n" + "="*80)
    
    conn.close()

if __name__ == "__main__":
    check_database()
