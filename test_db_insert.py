#!/usr/bin/env python3
"""
Test database insert to debug the issue
"""

import psycopg2
import json
from datetime import datetime, date

def test_insert():
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            database="tazara_multi_route",
            user="tazara",
            password="tazara123"
        )
        cursor = conn.cursor()
        
        # Test simple insert first
        print("🔍 Testing simple insert...")
        cursor.execute("""
            INSERT INTO multi_route_schedules (
                schedule_id, num_trains, total_days, cargo_requirements,
                daily_actions, train_assignments, performance_metrics,
                cost_breakdown_zmw, efficiency_analysis
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            'test_schedule_001',
            6,
            14,
            json.dumps({"DAR_KAPIRI": 1000}),
            json.dumps([[1,1,1]]),
            json.dumps([{"train_id": 0}]),
            json.dumps({"total_cargo_delivered": 500}),
            json.dumps({"revenue_zmw": 5000}),
            json.dumps({"cargo_per_train": 83.33})
        ))
        
        result = cursor.fetchone()
        print(f"✅ Insert successful! ID: {result[0] if result else 'None'}")
        
        # Commit the transaction
        conn.commit()
        
        # Check if it was saved
        cursor.execute("SELECT COUNT(*) FROM multi_route_schedules")
        count = cursor.fetchone()[0]
        print(f"📊 Total schedules now: {count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    test_insert()
