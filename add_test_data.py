#!/usr/bin/env python3
"""
Add performance history data for testing the dashboard
"""

import psycopg2
import json
from datetime import datetime, date

def add_performance_data():
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            database="tazara_multi_route",
            user="tazara",
            password="tazara123"
        )
        cursor = conn.cursor()
        
        # Add performance history for our test schedule
        print("🔍 Adding performance history data...")
        
        # Add performance history records for each route
        routes = ["DAR_KAPIRI", "DAR_MBEYA", "KAPIRI_NDOLA"]
        
        for route in routes:
            cursor.execute("""
                INSERT INTO performance_history (
                    schedule_id, metric_date, route_name, total_cargo_delivered,
                    trains_used, efficiency, net_profit_zmw
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                'test_schedule_001',
                date.today(),
                route,
                166.67,  # 500/3 distributed across routes
                2,       # trains used
                85.5,    # efficiency percentage
                25000    # profit
            ))
        
        # Commit the transaction
        conn.commit()
        
        # Check the data
        cursor.execute("SELECT COUNT(*) FROM performance_history")
        count = cursor.fetchone()[0]
        print(f"✅ Performance history records added: {count}")
        
        # Show the data
        cursor.execute("""
            SELECT route_name, total_cargo_delivered, efficiency 
            FROM performance_history 
            WHERE schedule_id = 'test_schedule_001'
        """)
        records = cursor.fetchall()
        print("📊 Performance data by route:")
        for record in records:
            print(f"  {record[0]}: {record[1]} tons, {record[2]}% efficiency")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    add_performance_data()
