from database.db_manager import db_manager

def check_db():
    print("Checking Database Tables for Performance History...")
    try:
        # Check performance_history
        history = db_manager.execute_query("SELECT * FROM performance_history LIMIT 5")
        print(f"\n📊 Performance History Rows: {len(history)}")
        for row in history:
            print(f"  - Date: {row.get('metric_date')}, Cargo: {row.get('total_cargo_delivered')}, Profit: {row.get('net_profit_zmw')}")

        # Check route_performance
        routes = db_manager.execute_query("SELECT * FROM route_performance LIMIT 5")
        print(f"\n📍 Route Performance Rows: {len(routes)}")
        for row in routes:
            print(f"  - Route: {row.get('route_name')}, Cargo: {row.get('cargo_delivered')}")

        if len(history) == 0:
            print("\n⚠️  No historical data found. Charts will show 'Mock Data' until you create a schedule.")
        else:
            print("\n✅ Data found! Graphs should now load correctly with the fixed queries.")

    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_db()
