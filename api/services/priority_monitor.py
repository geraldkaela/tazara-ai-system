"""
Priority Monitor Service for TAZARA AI Auto-Scheduling System
Continuously monitors orders for high-priority items and adds them to queue
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from .priority_scorer import EnhancedPriorityScorer

logger = logging.getLogger(__name__)

class PriorityMonitor:
    """Continuously monitors orders for high-priority items"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.check_interval = 300  # 5 minutes
        self.priority_threshold = 75.0
        self.priority_scorer = EnhancedPriorityScorer()
        self.running = False
        
        # Database connection
        self.conn = None
        
    async def start_monitoring(self):
        """Start the priority monitoring service"""
        if self.running:
            logger.warning("Priority monitor is already running")
            return
        
        self.running = True
        logger.info("Starting priority monitor service")
        
        try:
            # Initialize database connection
            await self._connect_database()
            
            # Main monitoring loop
            while self.running:
                try:
                    await self._check_for_high_priority_orders()
                    await asyncio.sleep(self.check_interval)
                    
                except Exception as e:
                    logger.error(f"Error in priority monitoring loop: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute on error
                    
        except Exception as e:
            logger.error(f"Fatal error in priority monitor: {e}")
            self.running = False
        finally:
            await self._close_database()
            logger.info("Priority monitor service stopped")
    
    async def stop_monitoring(self):
        """Stop the priority monitoring service"""
        self.running = False
        logger.info("Stopping priority monitor service")
    
    async def _connect_database(self):
        """Initialize database connection"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_config['host'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            logger.info("Priority monitor connected to database")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def _close_database(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Priority monitor database connection closed")
    
    async def _check_for_high_priority_orders(self):
        """Check for unscheduled high-priority orders"""
        try:
            if not self.conn:
                await self._connect_database()
            
            # Get unscheduled orders from customer_orders table
            unscheduled_orders = await self._get_unscheduled_orders()
            
            if not unscheduled_orders:
                logger.debug("No unscheduled orders found")
                return
            
            # Calculate priority scores
            scored_orders = self.priority_scorer.batch_calculate_scores(unscheduled_orders)
            
            # Filter high-priority orders
            high_priority_orders = self.priority_scorer.get_high_priority_orders(scored_orders)
            
            if not high_priority_orders:
                logger.debug("No high-priority orders found")
                return
            
            logger.info(f"Found {len(high_priority_orders)} high-priority orders")
            
            # Add to priority queue
            added_count = await self._add_to_priority_queue(high_priority_orders)
            logger.info(f"Added {added_count} orders to priority queue")
            
            # Update order statuses
            await self._update_order_statuses(high_priority_orders)
            
        except Exception as e:
            logger.error(f"Error checking for high-priority orders: {e}")
    
    async def _get_unscheduled_orders(self) -> List[Dict]:
        """Get unscheduled orders from customer_orders table"""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
            SELECT 
                order_id,
                customer_name,
                customer_tier,
                cargo_type,
                cargo_weight,
                cargo_value,
                route,
                delivery_deadline,
                created_at,
                metadata,
                status
            FROM customer_orders
            WHERE status IN ('pending', 'confirmed')
            AND created_at >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY created_at ASC
            """
            
            cursor.execute(query)
            orders = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            
            logger.debug(f"Retrieved {len(orders)} unscheduled orders")
            return orders
            
        except Exception as e:
            logger.error(f"Error getting unscheduled orders: {e}")
            return []
    
    async def _add_to_priority_queue(self, high_priority_orders: List[Dict]) -> int:
        """Add high-priority orders to priority queue"""
        try:
            cursor = self.conn.cursor()
            added_count = 0
            
            for order in high_priority_orders:
                # Check if already in priority queue
                if not await self._is_already_in_queue(order['order_id']):
                    # Insert into priority queue
                    insert_query = """
                    INSERT INTO priority_queue (
                        order_id, customer_name, customer_tier, cargo_type, cargo_weight,
                        cargo_value, route, priority_score, urgency_level, delivery_deadline,
                        created_at, status, priority_factors, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (order_id) DO UPDATE SET
                        priority_score = EXCLUDED.priority_score,
                        status = 'pending',
                        updated_at = CURRENT_TIMESTAMP
                    """
                    
                    cursor.execute(insert_query, (
                        order['order_id'],
                        order.get('customer_name', ''),
                        order['customer_tier'],
                        order.get('cargo_type', ''),
                        order.get('cargo_weight', 0),
                        order.get('cargo_value', 0),
                        order.get('route', ''),
                        order['priority_score'],
                        order['urgency_level'],
                        order.get('delivery_deadline'),
                        order['created_at'],
                        'pending',
                        order.get('factors', {}),
                        order.get('metadata', {})
                    ))
                    
                    added_count += 1
                    logger.debug(f"Added order {order['order_id']} to priority queue with score {order['priority_score']}")
            
            self.conn.commit()
            cursor.close()
            
            return added_count
            
        except Exception as e:
            logger.error(f"Error adding orders to priority queue: {e}")
            self.conn.rollback()
            return 0
    
    async def _is_already_in_queue(self, order_id: str) -> bool:
        """Check if order is already in priority queue"""
        try:
            cursor = self.conn.cursor()
            
            query = "SELECT 1 FROM priority_queue WHERE order_id = %s"
            cursor.execute(query, (order_id,))
            exists = cursor.fetchone() is not None
            cursor.close()
            
            return exists
            
        except Exception as e:
            logger.error(f"Error checking if order {order_id} is in queue: {e}")
            return False
    
    async def _update_order_statuses(self, high_priority_orders: List[Dict]):
        """Update original order statuses to show they're in priority queue"""
        try:
            cursor = self.conn.cursor()
            
            for order in high_priority_orders:
                update_query = """
                UPDATE customer_orders
                SET status = 'in_priority_queue',
                    updated_at = CURRENT_TIMESTAMP
                WHERE order_id = %s
                """
                
                cursor.execute(update_query, (order['order_id'],))
            
            self.conn.commit()
            cursor.close()
            
            logger.debug(f"Updated statuses for {len(high_priority_orders)} orders")
            
        except Exception as e:
            logger.error(f"Error updating order statuses: {e}")
            self.conn.rollback()
    
    async def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        try:
            if not self.conn:
                await self._connect_database()
            
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            # Get priority queue statistics
            stats_query = """
            SELECT 
                COUNT(*) as total_orders,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
                COUNT(CASE WHEN status = 'queued' THEN 1 END) as queued_orders,
                COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as scheduled_orders,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
                AVG(priority_score) as avg_priority_score,
                MAX(priority_score) as max_priority_score,
                COUNT(CASE WHEN urgency_level = 'emergency' THEN 1 END) as emergency_orders,
                COUNT(CASE WHEN delivery_deadline < CURRENT_TIMESTAMP + INTERVAL '24 hours' THEN 1 END) as urgent_deadline_orders
            FROM priority_queue
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            """
            
            cursor.execute(stats_query)
            stats = dict(cursor.fetchone())
            cursor.close()
            
            return {
                'monitoring_active': self.running,
                'check_interval_seconds': self.check_interval,
                'priority_threshold': self.priority_threshold,
                'last_check': datetime.now().isoformat(),
                'queue_statistics': stats,
                'database_connected': self.conn is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting monitoring status: {e}")
            return {
                'monitoring_active': False,
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    async def force_check(self):
        """Force an immediate check for high-priority orders"""
        logger.info("Forcing immediate priority check")
        await self._check_for_high_priority_orders()
    
    async def get_queue_health(self) -> Dict:
        """Get health status of priority queue"""
        try:
            if not self.conn:
                await self._connect_database()
            
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            # Check for stuck orders
            stuck_query = """
            SELECT COUNT(*) as stuck_orders
            FROM priority_queue
            WHERE status = 'pending'
            AND created_at < CURRENT_TIMESTAMP - INTERVAL '2 hours'
            """
            
            cursor.execute(stuck_query)
            stuck_count = cursor.fetchone()['stuck_orders']
            
            # Check queue size
            size_query = "SELECT COUNT(*) as queue_size FROM priority_queue WHERE status IN ('pending', 'queued')"
            cursor.execute(size_query)
            queue_size = cursor.fetchone()['queue_size']
            
            cursor.close()
            
            health_status = 'healthy'
            if stuck_count > 0:
                health_status = 'warning'
            if queue_size > 50:
                health_status = 'critical'
            
            return {
                'health_status': health_status,
                'queue_size': queue_size,
                'stuck_orders': stuck_count,
                'max_queue_size': 50,
                'check_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting queue health: {e}")
            return {
                'health_status': 'error',
                'error': str(e),
                'check_time': datetime.now().isoformat()
            }
