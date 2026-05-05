"""
Reset Orders to Pending for Testing
Reset some scheduled orders back to pending status for testing
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

def reset_orders_to_pending():
    """Reset some scheduled orders back to pending status"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Reset scheduled orders back to pending
        reset_query = """
        UPDATE customer_orders 
        SET status = 'pending', 
            updated_at = CURRENT_TIMESTAMP
        WHERE status = 'scheduled'
        """
        
        cursor.execute(reset_query)
        rows_affected = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Reset {rows_affected} orders back to pending status")
        
        # Check current status
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        status_query = """
        SELECT 
            COUNT(*) as total_orders,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
            COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as scheduled_orders
        FROM customer_orders
        """
        
        cursor.execute(status_query)
        stats = dict(cursor.fetchone())
        
        cursor.close()
        conn.close()
        
        print(f"Current status:")
        print(f"  Total orders: {stats['total_orders']}")
        print(f"  Pending orders: {stats['pending_orders']}")
        print(f"  Scheduled orders: {stats['scheduled_orders']}")
        
        return rows_affected > 0
        
    except Exception as e:
        print(f"Error resetting orders: {e}")
        return False

if __name__ == "__main__":
    reset_orders_to_pending()
