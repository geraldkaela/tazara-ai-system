#!/usr/bin/env python3
"""
Test script to verify departure dates are working correctly
"""

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': 'localhost',
    'database': 'tazara_multi_route',
    'user': 'tazara',
    'password': 'tazara123'
}

def test_departure_dates():
    """Test that departure dates are stored and retrieved correctly"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if departure_date column exists
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'daily_assignments' 
            AND column_name = 'departure_date'
        """)
        column_info = cursor.fetchone()
        
        if column_info:
            print(f"✅ departure_date column exists: {column_info['data_type']}")
        else:
            print("❌ departure_date column not found")
            return
        
        # Get recent assignments with departure dates
        cursor.execute("""
            SELECT schedule_id, day, train_id, route, departure_date, created_at
            FROM daily_assignments 
            WHERE departure_date IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        assignments = cursor.fetchall()
        
        if assignments:
            print(f"\n📋 Found {len(assignments)} assignments with departure dates:")
            for assignment in assignments:
                print(f"  • {assignment['schedule_id']} - Day {assignment['day']} - {assignment['train_id']} - {assignment['route']}")
                print(f"    Departure: {assignment['departure_date']}")
        else:
            print("\n📋 No assignments with departure dates found")
        
        # Check orders with requested departure dates
        cursor.execute("""
            SELECT order_id, origin_station, destination_station, requested_departure_date
            FROM customer_orders
            WHERE requested_departure_date IS NOT NULL
            AND status = 'scheduled'
            ORDER BY updated_at DESC
            LIMIT 5
        """)
        
        orders = cursor.fetchall()
        
        if orders:
            print(f"\n📦 Found {len(orders)} scheduled orders with requested departure dates:")
            for order in orders:
                print(f"  • {order['order_id']} - {order['origin_station']} to {order['destination_station']}")
                print(f"    Requested departure: {order['requested_departure_date']}")
        else:
            print("\n📦 No scheduled orders with requested departure dates found")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_departure_dates()
