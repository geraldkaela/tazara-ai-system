"""
Simple Priority System Test
Tests basic database connection and functionality
"""

import psycopg2
import json
from datetime import datetime, timedelta
import os
import sys

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'tazara_multi_route',
    'user': 'tazara',
    'password': 'tazara123'
}

def test_priority_queue_status():
    """Test priority queue status"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if priority queue table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'priority_queue'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("Priority queue table exists")
            
            # Get queue status
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_orders,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
                    COUNT(CASE WHEN status = 'queued' THEN 1 END) as queued_orders,
                    AVG(priority_score) as avg_priority_score,
                    MAX(priority_score) as max_priority_score
                FROM priority_queue
            """)
            
            stats = cursor.fetchone()
            print(f"Queue Status:")
            print(f"  Total Orders: {stats[0]}")
            print(f"  Pending Orders: {stats[1]}")
            print(f"  Queued Orders: {stats[2]}")
            print(f"  Avg Priority Score: {stats[3]}")
            print(f"  Max Priority Score: {stats[4]}")
            
            # Get sample orders
            cursor.execute("""
                SELECT order_id, customer_name, priority_score, urgency_level, status
                FROM priority_queue
                ORDER BY priority_score DESC
                LIMIT 5
            """)
            
            orders = cursor.fetchall()
            print(f"\nSample Orders:")
            for order in orders:
                print(f"  {order[0]} - {order[1]} - Score: {order[2]} - {order[3]} - {order[4]}")
            
            return True
        else:
            print("Priority queue table does not exist")
            return False
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error testing priority queue: {e}")
        return False

def test_api_endpoints():
    """Test if we can import API modules"""
    try:
        # Try importing main API
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        import api.main
        print("Main API imported successfully")
        
        # Check if priority router is included
        from api.main import app
        routes = [route.path for route in app.routes]
        
        priority_routes = [r for r in routes if 'priority' in r]
        print(f"Priority routes found: {priority_routes}")
        
        return True
        
    except Exception as e:
        print(f"Error importing API: {e}")
        return False

def main():
    """Main test function"""
    print("TAZARA Priority System - Simple Test")
    print("=" * 50)
    
    # Test database connection
    print("\n1. Testing Database Connection...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        print("Database connection: SUCCESS")
    except Exception as e:
        print(f"Database connection: FAILED - {e}")
        return
    
    # Test priority queue
    print("\n2. Testing Priority Queue...")
    if test_priority_queue_status():
        print("Priority queue: SUCCESS")
    else:
        print("Priority queue: FAILED")
    
    # Test API imports
    print("\n3. Testing API Imports...")
    if test_api_endpoints():
        print("API imports: SUCCESS")
    else:
        print("API imports: FAILED")
    
    print("\n" + "=" * 50)
    print("Test Complete!")
    print("\nNext Steps:")
    print("1. Start main API: python -m uvicorn api.main:app --reload")
    print("2. Visit: http://127.0.0.1:8000/priority/queue/status")
    print("3. Visit: http://127.0.0.1:8000/dashboard/multi_route.html")

if __name__ == "__main__":
    main()
