import psycopg2
import requests
import os
import json

# Configuration
DB_URL = os.getenv('DATABASE_URL', 'postgresql://tazara:tazara123@localhost:5432/tazara_multi_route')
API_URL = "http://127.0.0.1:8000/multi-route/dashboard/stats"

def get_db_stats():
    """Get metrics directly from PostgreSQL"""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # 1. Total Cargo
        cursor.execute("""
            SELECT SUM((performance_metrics->>'total_cargo_delivered')::numeric) 
            FROM multi_route_schedules 
            WHERE status = 'active'
        """)
        total_cargo = float(cursor.fetchone()[0] or 0)
        
        # 2. Avg Efficiency
        cursor.execute("""
            SELECT AVG((performance_metrics->>'efficiency')::numeric) 
            FROM multi_route_schedules 
            WHERE status = 'active'
        """)
        avg_efficiency = float(cursor.fetchone()[0] or 0)
        
        # 3. Total Profit (Average profit as per db_manager logic)
        cursor.execute("""
            SELECT AVG((cost_breakdown_zmw->>'net_profit_zmw')::numeric) 
            FROM multi_route_schedules 
            WHERE status = 'active'
        """)
        avg_profit = float(cursor.fetchone()[0] or 0)
        
        conn.close()
        return {
            "total_cargo_delivered": total_cargo,
            "average_efficiency": avg_efficiency,
            "average_profit": avg_profit
        }
    except Exception as e:
        print(f"Postgres Error: {e}")
        return None

def main():
    print("=" * 60)
    print("VERIFYING HOME PAGE DATA (index.html)")
    print("=" * 60)
    
    # Get DB data
    db_data = get_db_stats()
    if not db_data:
        return
    
    # Get API data
    try:
        response = requests.get(API_URL)
        api_data = response.json()
    except Exception as e:
        print(f"API Error: {e}")
        return

    print(f"\nComparing PostgreSQL results vs API response...")
    
    metrics = [
        ("Total Cargo", "total_cargo_delivered"),
        ("Avg Efficiency", "average_efficiency"),
        ("Avg Profit", "average_profit")
    ]
    
    all_pass = True
    for label, key in metrics:
        db_val = db_data.get(key, 0)
        api_val = api_data.get(key, 0)
        
        status = "✅ PASS" if abs(db_val - api_val) < 0.01 else "❌ FAIL"
        if status == "❌ FAIL": all_pass = False
        
        print(f"  {label:15}: DB={db_val:<10} | API={api_val:<10} | {status}")

    if all_pass:
        print("\n✨ VERIFICATION SUCCESSFUL: Home Page metrics match Postgres.")
    else:
        print("\n⚠️ VERIFICATION FAILED: Discrepancies detected.")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
