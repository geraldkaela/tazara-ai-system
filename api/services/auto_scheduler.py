"""
Auto-Scheduler Service for TAZARA AI Priority System
Automatically schedules high-priority orders using AI optimization
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from .priority_scorer import EnhancedPriorityScorer

logger = logging.getLogger(__name__)

class AutoScheduler:
    """Automatically schedules high-priority orders"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.available_trains = 12
        self.max_cargo_per_batch = 12000  # Max cargo per batch
        self.scheduling_interval = 600  # 10 minutes
        self.priority_scorer = EnhancedPriorityScorer()
        self.running = False
        
        # Database connection
        self.conn = None
        
        # Import existing scheduling functions
        from ..routes.multi_route import create_multi_route_schedule, MultiRouteRequest
        self.create_schedule = create_multi_route_schedule
        self.ScheduleRequest = MultiRouteRequest
    
    async def start_auto_scheduling(self):
        """Start the auto-scheduling service"""
        if self.running:
            logger.warning("Auto-scheduler is already running")
            return
        
        self.running = True
        logger.info("Starting auto-scheduler service")
        
        try:
            # Initialize database connection
            await self._connect_database()
            
            # Main auto-scheduling loop
            while self.running:
                try:
                    # Get next batch of high-priority orders
                    order_batch = await self._get_next_priority_batch()
                    
                    if order_batch:
                        logger.info(f"Processing priority batch with {len(order_batch)} orders")
                        
                        # Create schedule for this batch
                        schedule_result = await self._create_priority_schedule(order_batch)
                        
                        if schedule_result['success']:
                            # Execute schedule
                            await self._execute_schedule(schedule_result['schedule'])
                            
                            # Update order statuses
                            await self._update_order_statuses(order_batch, schedule_result['schedule'])
                            
                            # Send notifications
                            await self._send_priority_notifications(schedule_result['schedule'])
                            
                            logger.info(f"Successfully scheduled priority batch: {schedule_result['schedule']['schedule_id']}")
                        else:
                            logger.error(f"Failed to create priority schedule: {schedule_result['error']}")
                    
                    await asyncio.sleep(self.scheduling_interval)
                    
                except Exception as e:
                    logger.error(f"Error in auto-scheduling loop: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute on error
                    
        except Exception as e:
            logger.error(f"Fatal error in auto-scheduler: {e}")
            self.running = False
        finally:
            await self._close_database()
            logger.info("Auto-scheduler service stopped")
    
    async def stop_auto_scheduling(self):
        """Stop the auto-scheduling service"""
        self.running = False
        logger.info("Stopping auto-scheduler service")
    
    async def _connect_database(self):
        """Initialize database connection"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_config['host'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            logger.info("Auto-scheduler connected to database")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def _close_database(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Auto-scheduler database connection closed")
    
    async def _get_next_priority_batch(self) -> Optional[List[Dict]]:
        """Get next batch of high-priority orders for scheduling"""
        try:
            if not self.conn:
                await self._connect_database()
            
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            # Use the database function to get next batch
            query = """
            SELECT * FROM get_priority_batch(%s, %s)
            """
            
            cursor.execute(query, (self.available_trains, self.max_cargo_per_batch))
            result = cursor.fetchone()
            cursor.close()
            
            if result and result['order_ids']:
                # Convert to list of order objects
                orders = []
                for i, order_id in enumerate(result['order_ids']):
                    order = {
                        'order_id': order_id,
                        'priority_score': result['priority_scores'][i],
                        'deadline_earliest': result['deadline_earliest'],
                        'deadline_latest': result['deadline_latest']
                    }
                    
                    # Get full order details
                    full_order = await self._get_order_details(order_id)
                    if full_order:
                        order.update(full_order)
                        orders.append(order)
                
                return orders
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting priority batch: {e}")
            return None
    
    async def _get_order_details(self, order_id: str) -> Optional[Dict]:
        """Get detailed order information"""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
            SELECT 
                order_id, customer_name, customer_tier, cargo_type,
                cargo_weight, cargo_value, route, delivery_deadline,
                created_at, metadata, status
            FROM customer_orders
            WHERE order_id = %s
            """
            
            cursor.execute(query, (order_id,))
            order = dict(cursor.fetchone())
            cursor.close()
            
            return order
            
        except Exception as e:
            logger.error(f"Error getting order details for {order_id}: {e}")
            return None
    
    async def _create_priority_schedule(self, order_batch: List[Dict]) -> Dict:
        """Create schedule for priority order batch"""
        try:
            # Aggregate cargo requirements from batch
            aggregated_cargo = self._aggregate_cargo_requirements(order_batch)
            
            # Calculate optimal scheduling days based on deadlines
            max_days = self._calculate_optimal_days(order_batch)
            
            # Create schedule request with priority metadata
            schedule_request = self.ScheduleRequest(
                num_trains=min(self.available_trains, len(order_batch)),
                max_days=max_days,
                cargo_requirements=aggregated_cargo,
                use_deep_rl=True,
                metadata={
                    'auto_scheduled': True,
                    'priority_batch': [order['order_id'] for order in order_batch],
                    'priority_scores': [order['priority_score'] for order in order_batch],
                    'based_on_orders': True,
                    'deadline_earliest': min(order['deadline_earliest'] for order in order_batch),
                    'deadline_latest': max(order['deadline_latest'] for order in order_batch),
                    'batch_created_at': datetime.now().isoformat()
                }
            )
            
            # Use existing scheduling endpoint
            schedule = await self.create_schedule(schedule_request)
            
            return {
                'success': True,
                'schedule': schedule,
                'order_batch': order_batch,
                'aggregated_cargo': aggregated_cargo
            }
            
        except Exception as e:
            logger.error(f"Error creating priority schedule: {e}")
            return {
                'success': False,
                'error': str(e),
                'order_batch': order_batch
            }
    
    def _aggregate_cargo_requirements(self, order_batch: List[Dict]) -> Dict[str, float]:
        """Aggregate cargo requirements from order batch"""
        cargo_by_route = {}
        
        for order in order_batch:
            route = order.get('route', 'UNKNOWN')
            cargo_weight = order.get('cargo_weight', 0)
            
            if route not in cargo_by_route:
                cargo_by_route[route] = 0
            cargo_by_route[route] += cargo_weight
        
        return cargo_by_route
    
    def _calculate_optimal_days(self, order_batch: List[Dict]) -> int:
        """Calculate optimal number of days based on deadlines"""
        if not order_batch:
            return 7  # Default
        
        # Find earliest deadline
        earliest_deadline = min(
            datetime.fromisoformat(order['deadline_earliest'].replace('Z', '+00:00'))
            for order in order_batch
        )
        
        # Calculate days needed with buffer
        days_until_deadline = (earliest_deadline - datetime.now()).days
        optimal_days = max(3, days_until_deadline - 1)  # 1 day buffer
        
        # Cap at 14 days
        return min(optimal_days, 14)
    
    async def _execute_schedule(self, schedule: Dict):
        """Execute the created schedule"""
        try:
            cursor = self.conn.cursor()
            
            # Record schedule execution
            insert_query = """
            INSERT INTO priority_scheduling_history (
                schedule_id, order_ids, priority_scores, total_cargo_weight,
                total_trains_used, scheduled_at, status, performance_metrics
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                schedule['schedule_id'],
                schedule['metadata']['priority_batch'],
                schedule['metadata']['priority_scores'],
                sum(schedule['efficiency_analysis'].get('cargo_delivered', 0).values()) if isinstance(schedule['efficiency_analysis'].get('cargo_delivered'), dict) else schedule['efficiency_analysis'].get('cargo_delivered', 0),
                schedule['efficiency_analysis'].get('num_trains', 0),
                datetime.now(),
                'in_progress',
                schedule['efficiency_analysis'],
                schedule['cost_breakdown_zmw']
            ))
            
            self.conn.commit()
            cursor.close()
            
            logger.info(f"Schedule {schedule['schedule_id']} executed and recorded")
            
        except Exception as e:
            logger.error(f"Error executing schedule {schedule.get('schedule_id', 'unknown')}: {e}")
            self.conn.rollback()
    
    async def _update_order_statuses(self, order_batch: List[Dict], schedule: Dict):
        """Update order statuses to scheduled"""
        try:
            cursor = self.conn.cursor()
            
            for order in order_batch:
                # Update customer_orders table
                update_query = """
                UPDATE customer_orders
                SET status = 'scheduled',
                    schedule_id = %s,
                    scheduled_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE order_id = %s
                """
                
                cursor.execute(update_query, (schedule['schedule_id'], order['order_id']))
            
            # Update priority_queue table
                priority_update_query = """
                UPDATE priority_queue
                SET status = 'scheduled',
                    scheduled_at = CURRENT_TIMESTAMP,
                    schedule_id = %s
                WHERE order_id = %s
                """
                
                cursor.execute(priority_update_query, (schedule['schedule_id'], order['order_id']))
            
            self.conn.commit()
            cursor.close()
            
            logger.info(f"Updated statuses for {len(order_batch)} orders")
            
        except Exception as e:
            logger.error(f"Error updating order statuses: {e}")
            self.conn.rollback()
    
    async def _send_priority_notifications(self, schedule: Dict):
        """Send notifications for priority scheduling"""
        try:
            # Create notification data
            notification = {
                'type': 'priority_scheduled',
                'schedule_id': schedule['schedule_id'],
                'orders': schedule['metadata']['priority_batch'],
                'priority_scores': schedule['metadata']['priority_scores'],
                'scheduled_at': datetime.now().isoformat(),
                'total_cargo': schedule['cargo_delivered'],
                'total_profit': schedule['total_profit'],
                'efficiency': schedule['efficiency_analysis'].get('efficiency', 0),
                'deadline_compliance': self._check_deadline_compliance(schedule)
            }
            
            # Log notification
            logger.info(f"Priority scheduling notification: {notification}")
            
            # Here you could integrate with:
            # - WebSocket notifications
            # - Email notifications
            # - SMS notifications
            # - Dashboard alerts
            
            return notification
            
        except Exception as e:
            logger.error(f"Error sending priority notifications: {e}")
    
    def _check_deadline_compliance(self, schedule: Dict) -> Dict:
        """Check if schedule meets order deadlines"""
        try:
            metadata = schedule.get('metadata', {})
            deadline_earliest = metadata.get('deadline_earliest')
            
            if not deadline_earliest:
                return {'compliant': False, 'reason': 'No deadline information'}
            
            deadline_date = datetime.fromisoformat(deadline_earliest.replace('Z', '+00:00'))
            scheduled_date = datetime.now()
            
            # Calculate completion time (schedule duration)
            max_days = schedule.get('max_days', 7)
            completion_date = scheduled_date + timedelta(days=max_days)
            
            is_compliant = completion_date <= deadline_date
            days_buffer = (deadline_date - completion_date).days
            
            return {
                'compliant': is_compliant,
                'deadline': deadline_earliest,
                'completion': completion_date.isoformat(),
                'days_buffer': days_buffer,
                'risk_level': 'low' if days_buffer > 0 else 'high'
            }
            
        except Exception as e:
            logger.error(f"Error checking deadline compliance: {e}")
            return {'compliant': False, 'reason': str(e)}
    
    async def get_scheduling_status(self) -> Dict:
        """Get current auto-scheduling status"""
        try:
            if not self.conn:
                await self._connect_database()
            
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            # Get recent scheduling history
            history_query = """
            SELECT 
                COUNT(*) as total_schedules,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_schedules,
                COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_schedules,
                AVG(scheduling_duration_ms) as avg_duration_ms,
                MAX(scheduled_at) as last_schedule,
                SUM(total_cargo_weight) as total_cargo_scheduled
            FROM priority_scheduling_history
            WHERE scheduled_at >= CURRENT_DATE - INTERVAL '7 days'
            """
            
            cursor.execute(history_query)
            history = dict(cursor.fetchone())
            
            # Get current queue status
            queue_query = """
            SELECT 
                COUNT(*) as queue_size,
                AVG(priority_score) as avg_priority_score,
                COUNT(CASE WHEN urgency_level = 'emergency' THEN 1 END) as emergency_orders
            FROM priority_queue
            WHERE status IN ('pending', 'queued')
            """
            
            cursor.execute(queue_query)
            queue = dict(cursor.fetchone())
            
            cursor.close()
            
            return {
                'auto_scheduling_active': self.running,
                'scheduling_interval': self.scheduling_interval,
                'available_trains': self.available_trains,
                'max_cargo_per_batch': self.max_cargo_per_batch,
                'recent_performance': history,
                'current_queue': queue,
                'database_connected': self.conn is not None,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting scheduling status: {e}")
            return {
                'auto_scheduling_active': False,
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    async def force_schedule_batch(self, order_ids: List[str]) -> Dict:
        """Force scheduling of specific orders"""
        try:
            # Get order details
            orders = []
            for order_id in order_ids:
                order = await self._get_order_details(order_id)
                if order:
                    # Calculate priority score
                    scored_order = self.priority_scorer.calculate_priority_score(order)
                    order.update(scored_order)
                    orders.append(order)
            
            if not orders:
                return {'success': False, 'error': 'No valid orders found'}
            
            # Create schedule
            result = await self._create_priority_schedule(orders)
            
            if result['success']:
                await self._execute_schedule(result['schedule'])
                await self._update_order_statuses(orders, result['schedule'])
                await self._send_priority_notifications(result['schedule'])
            
            logger.info(f"Force scheduled batch: {order_ids}")
            return result
            
        except Exception as e:
            logger.error(f"Error force scheduling batch {order_ids}: {e}")
            return {'success': False, 'error': str(e)}
