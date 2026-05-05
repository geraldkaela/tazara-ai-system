import sqlite3
import psycopg2
import psycopg2.extras
import os
import json
from pathlib import Path

def dump_sqlite():
    print("=" * 60)
    print("SQLITE CONTENTS: database/tazara.db")
    print("=" * 60)
    db_path = Path("database/tazara.db")
    if not db_path.exists():
        print("SQLite DB not found.")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check Risk Analysis
    print("\n[ Table: risk_analysis ] (Top 3)")
    cursor.execute("SELECT analysis_date, risk_score, risk_level FROM risk_analysis LIMIT 3")
    for row in cursor.fetchall():
        print(f"  Date: {row['analysis_date']} | Score: {row['risk_score']} | Level: {row['risk_level']}")

    # Check Forecasting Models
    print("\n[ Table: forecasting_models ]")
    cursor.execute("SELECT model_name, model_type, rmse, is_active FROM forecasting_models")
    for row in cursor.fetchall():
        print(f"  Model: {row['model_name']} | Type: {row['model_type']} | RMSE: {row['rmse']} | Active: {row['is_active']}")

    conn.close()

def dump_postgres():
    print("\n" + "=" * 60)
    print("POSTGRES CONTENTS: tazara_multi_route")
    print("=" * 60)
    db_url = os.getenv('DATABASE_URL', 'postgresql://tazara:tazara123@localhost:5432/tazara_multi_route')
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Check Multi-Route Schedules
        print("\n[ Table: multi_route_schedules ] (Top 2)")
        cursor.execute("SELECT schedule_id, timestamp, status FROM multi_route_schedules LIMIT 2")
        for row in cursor.fetchall():
            print(f"  ID: {row['schedule_id']} | Date: {row['timestamp']} | Status: {row['status']}")

        # Check Performance History
        print("\n[ Table: performance_history ] (Top 5)")
        cursor.execute("SELECT schedule_id, metric_date, route_name, total_cargo_delivered, net_profit_zmw FROM performance_history LIMIT 5")
        for row in cursor.fetchall():
            print(f"  Schedule: {row['schedule_id']} | Date: {row['metric_date']} | Route: {row['route_name']} | Cargo: {row['total_cargo_delivered']} | Profit: {row['net_profit_zmw']}")

        conn.close()
    except Exception as e:
        print(f"Postgres error: {e}")

if __name__ == "__main__":
    dump_sqlite()
    dump_postgres()
