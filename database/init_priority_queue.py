"""
Priority Queue Database Initialization Script
Creates and populates the priority queue database schema
"""

import psycopg2
import logging
import os
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'tazara_multi_route',
    'user': 'tazara',
    'password': 'tazara123'
}

def init_priority_queue_database():
    """Initialize priority queue database schema"""
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Read and execute schema
        schema_path = os.path.join(os.path.dirname(__file__), 'priority_queue_schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema
        cursor.execute(schema_sql)
        
        # Commit changes
        conn.commit()
        
        # Close connection
        cursor.close()
        conn.close()
        
        logger.info("Priority queue database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize priority queue database: {e}")
        return False

def create_sample_orders():
    """Create sample high-priority orders for testing"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Sample orders for testing
        sample_orders = [
            {
                'order_id': 'EMERGENCY_MEDICAL_001',
                'customer_name': 'Ministry of Health',
                'customer_tier': 'platinum',
                'cargo_type': 'Medical Supplies',
                'cargo_weight': 500.0,
                'cargo_value': 2500000.00,
                'route': 'DAR_KAPIRI',
                'priority_score': 92.5,
                'urgency_level': 'emergency',
                'delivery_deadline': datetime.now().isoformat(),
                'status': 'pending',
                'priority_factors': {
                    'urgency': {'level': 'emergency', 'score': 40},
                    'customer_tier': {'tier': 'platinum', 'score': 30},
                    'deadline': {'category': 'critical', 'score': 20},
                    'waiting_time': {'hours': 0, 'points': 0},
                    'special_factors': {'score': 2, 'details': 'medical supplies'}
                },
                'metadata': {
                    'contract_type': 'government',
                    'cargo_category': 'medical',
                    'perishable': False,
                    'security_level': 'high'
                }
            },
            {
                'order_id': 'URGENT_COPPER_002',
                'customer_name': 'Copperbelt Corporation',
                'customer_tier': 'gold',
                'cargo_type': 'Copper Ore',
                'cargo_weight': 1200.0,
                'cargo_value': 8500000.00,
                'route': 'KAPIRI_NDOLA',
                'priority_score': 77.5,
                'urgency_level': 'urgent',
                'delivery_deadline': (datetime.now() + timedelta(days=3)).isoformat(),
                'status': 'pending',
                'priority_factors': {
                    'urgency': {'level': 'urgent', 'score': 30},
                    'customer_tier': {'tier': 'gold', 'score': 20},
                    'deadline': {'category': 'urgent', 'score': 15},
                    'waiting_time': {'hours': 0, 'points': 0},
                    'special_factors': {'score': 1, 'details': 'high value copper'}
                },
                'metadata': {
                    'contract_type': 'commercial',
                    'cargo_category': 'minerals',
                    'perishable': False,
                    'security_level': 'medium'
                }
            },
            {
                'order_id': 'PRIORITY_FUEL_003',
                'customer_name': 'Energy Solutions Ltd',
                'customer_tier': 'silver',
                'cargo_type': 'Petroleum Products',
                'cargo_weight': 800.0,
                'cargo_value': 1200000.00,
                'route': 'DAR_MBEYA',
                'priority_score': 62.5,
                'urgency_level': 'priority',
                'delivery_deadline': (datetime.now() + timedelta(days=7)).isoformat(),
                'status': 'pending',
                'priority_factors': {
                    'urgency': {'level': 'priority', 'score': 20},
                    'customer_tier': {'tier': 'silver', 'score': 10},
                    'deadline': {'category': 'high', 'score': 10},
                    'waiting_time': {'hours': 0, 'points': 0},
                    'special_factors': {'score': 1, 'details': 'energy sector'}
                },
                'metadata': {
                    'contract_type': 'commercial',
                    'cargo_category': 'fuels',
                    'perishable': False,
                    'security_level': 'high'
                }
            }
        ]
        
        # Insert sample orders
        for order in sample_orders:
            insert_query = """
            INSERT INTO priority_queue (
                order_id, customer_name, customer_tier, cargo_type, cargo_weight,
                cargo_value, route, priority_score, urgency_level, delivery_deadline,
                created_at, status, priority_factors, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (order_id) DO NOTHING
            """
            
            cursor.execute(insert_query, (
                order['order_id'],
                order['customer_name'],
                order['customer_tier'],
                order['cargo_type'],
                order['cargo_weight'],
                order['cargo_value'],
                order['route'],
                order['priority_score'],
                order['urgency_level'],
                order['delivery_deadline'],
                datetime.now(),
                order['status'],
                json.dumps(order['priority_factors']),
                json.dumps(order['metadata'])
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Created {len(sample_orders)} sample priority orders")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create sample orders: {e}")
        return False

def test_priority_functions():
    """Test priority queue database functions"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Test add_to_priority_queue function
        test_order_id = 'TEST_ORDER_001'
        cursor.execute("SELECT add_to_priority_queue(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                      (test_order_id, 'Test Customer', 'gold', 'Test Cargo', 500.0, 100000.0, 'DAR_KAPIRI', 85.0, 'priority', datetime.now(), '{"test": true}', '{"test": true}'))
        
        result = cursor.fetchone()
        if result:
            logger.info(f"Test add_to_priority_queue result: {result[0]}")
        else:
            logger.info("Test add_to_priority_queue result: No result returned")
        
        # Test get_priority_batch function
        cursor.execute("SELECT * FROM get_priority_batch(6, 6000)")
        batch_result = cursor.fetchone()
        if batch_result:
            logger.info(f"Test get_priority_batch result: {batch_result}")
        else:
            logger.info("Test get_priority_batch result: No batch available")
        
        # Test priority queue stats view
        cursor.execute("SELECT * FROM priority_queue_stats")
        stats = cursor.fetchone()
        if stats:
            logger.info(f"Test priority_queue_stats result: {stats}")
        else:
            logger.info("Test priority_queue_stats result: No stats available")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("Priority queue functions tested successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to test priority functions: {e}")
        return False

if __name__ == "__main__":
    print("Initializing TAZARA Priority Queue Database...")
    
    # Initialize database schema
    if init_priority_queue_database():
        print("✅ Database schema initialized successfully")
        
        # Create sample data
        if create_sample_orders():
            print("✅ Sample orders created successfully")
            
            # Test functions
            if test_priority_functions():
                print("✅ Priority functions tested successfully")
                
                print("\n🎉 Priority Queue Database Initialization Complete!")
                print("📊 Ready for auto-scheduling implementation")
            else:
                print("❌ Priority function tests failed")
        else:
            print("❌ Failed to create sample orders")
    else:
        print("❌ Failed to initialize database schema")
