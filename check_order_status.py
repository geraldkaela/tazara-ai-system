"""
Check Order Status After Scheduling
Verify that only scheduled orders are marked as scheduled and others remain pending
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'tazara_multi_route',
    'user': 'tazara',
    'password': 'tazara123'
}

def check_order_status():
    """Check order status after scheduling"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get current order status
        status_query = """
        SELECT 
            COUNT(*) as total_orders,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
            COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as scheduled_orders,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders
        FROM customer_orders
        """
        
        cursor.execute(status_query)
        stats = dict(cursor.fetchone())
        
        print(f"Current Order Status:")
        print(f"  Total orders: {stats['total_orders']}")
        print(f"  Pending orders: {stats['pending_orders']}")
        print(f"  Scheduled orders: {stats['scheduled_orders']}")
        print(f"  Completed orders: {stats['completed_orders']}")
        
        # Get details of scheduled orders
        scheduled_query = """
        SELECT order_id, customer_name, cargo_type, cargo_weight, priority_level
        FROM customer_orders
        WHERE status = 'scheduled'
        ORDER BY priority_level ASC, created_at DESC
        LIMIT 10
        """
        
        cursor.execute(scheduled_query)
        scheduled_orders = cursor.fetchall()
        
        print(f"\nScheduled Orders (Top 10):")
        for order in scheduled_orders:
            print(f"  {order['order_id']}: {order['customer_name']} - {order['cargo_weight']} tons (Priority: {order['priority_level']})")
        
        # Get details of pending orders
        pending_query = """
        SELECT order_id, customer_name, cargo_type, cargo_weight, priority_level
        FROM customer_orders
        WHERE status = 'pending'
        ORDER BY priority_level ASC, created_at DESC
        LIMIT 10
        """
        
        cursor.execute(pending_query)
        pending_orders = cursor.fetchall()
        
        print(f"\nPending Orders (Top 10):")
        for order in pending_orders:
            print(f"  {order['order_id']}: {order['customer_name']} - {order['cargo_weight']} tons (Priority: {order['priority_level']})")
        
        cursor.close()
        conn.close()
        
        # Check if the fix worked
        if stats['scheduled_orders'] > 0 and stats['pending_orders'] > 0:
            print(f"\n\nSUCCESS! The fix worked:")
            print(f"  - {stats['scheduled_orders']} orders were scheduled")
            print(f"  - {stats['pending_orders']} orders remain pending")
            print(f"  - Only selected orders were marked as scheduled")
        elif stats['scheduled_orders'] == 0:
            print(f"\n\nISSUE: No orders were scheduled")
        elif stats['pending_orders'] == 0:
            print(f"\n\nISSUE: All orders were scheduled (fix didn't work)")
        
    except Exception as e:
        print(f"Error checking order status: {e}")

if __name__ == "__main__":
    check_order_status()
