import psycopg2
import requests
import os

# Configuration
DB_URL = os.getenv('DATABASE_URL', 'postgresql://tazara:tazara123@localhost:5432/tazara_multi_route')
TRENDS_API = "http://127.0.0.1:8000/multi-route/performance/trends"
ROUTES_API = "http://127.0.0.1:8000/multi-route/performance/routes"

def get_db_trends():
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                DATE(created_at) as performance_date,
                AVG(total_cargo_delivered) as avg_cargo,
                SUM(net_profit_zmw) as total_profit
            FROM performance_history 
            GROUP BY DATE(created_at)
            ORDER BY performance_date DESC
        """)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Postgres Trends Error: {e}")
        return []

def get_db_route_summary():
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                route_name,
                AVG(total_cargo_delivered) as avg_cargo,
                AVG(efficiency) as avg_efficiency
            FROM performance_history 
            GROUP BY route_name
        """)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Postgres Routes Error: {e}")
        return []

def main():
    print("=" * 60)
    print("VERIFYING MULTI-ROUTE DATA (multi_route.html)")
    print("=" * 60)
    
    # Verify Trends
    print("\n--- PERFORMANCE TRENDS ---")
    db_trends = get_db_trends()
    try:
        api_trends = requests.get(TRENDS_API).json().get('trends', [])
    except:
        api_trends = []
    
    print(f"DB Records: {len(db_trends)} | API Records: {len(api_trends)}")
    if len(db_trends) == len(api_trends):
        print("✅ PASS: Trend record counts match.")
    else:
        print("❌ FAIL: Trend record counts mismatch.")

    # Verify Route Summary
    print("\n--- ROUTE SUMMARIES ---")
    db_routes = get_db_route_summary()
    try:
        api_routes = requests.get(ROUTES_API).json().get('route_performance', [])
    except:
        api_routes = []
        
    db_route_dict = {r[0]: r[1] for r in db_routes} # total_cargo is index 1 in the local query
    api_route_dict = {r['route_name']: r['total_cargo'] for r in api_routes}
    
    all_routes_pass = True
    for route, db_cargo in db_route_dict.items():
        api_cargo = api_route_dict.get(route, 0)
        # Handle decimal vs float comparison
        status = "✅ PASS" if abs(float(db_cargo) - float(api_cargo)) < 0.1 else "❌ FAIL"
        print(f"  {route:15}: DB Cargo={float(db_cargo):<8.2f} | API Cargo={float(api_cargo):<8.2f} | {status}")
        if status == "❌ FAIL": all_routes_pass = False

    if all_routes_pass and len(db_route_dict) > 0:
        print("\n✨ VERIFICATION SUCCESSFUL: Route data matches Postgres.")
    elif len(db_route_dict) == 0:
        print("\nℹ️ No history data found in Postgres.")
    else:
        print("\n⚠️ VERIFICATION FAILED: Discrepancies in route data.")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
