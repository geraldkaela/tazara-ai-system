"""
TAZARA Multi-Route Database Manager
Phase 2 - Database Backend Integration
Phase 1 Enhancement: Labor Cost Optimization Support
"""

import psycopg2
import psycopg2.extras
import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager
import logging
from api.db_utils import get_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and operations manager for multi-route system"""
    
    def __init__(self, db_url: str = None):
        """Initialize database connection"""
        self.db_url = None
        self.connection = None
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        conn = get_db_connection()
        conn.autocommit = True
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: Tuple = None) -> List[Dict]:
        """Execute a query and return results as list of dictionaries"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def execute_insert(self, query: str, params: Tuple = None) -> Optional[str]:
        """Execute an insert query and return the ID if possible"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    try:
                        result = cursor.fetchone()
                        return result[0] if result else None
                    except (psycopg2.ProgrammingError, psycopg2.InternalError):
                        return None
        except Exception as e:
            logger.error(f"Insert execution error: {e}")
            raise
    
    def initialize_database(self, schema_file: str = None):
        """Initialize database with schema"""
        try:
            schema_file = schema_file or os.path.join(
                os.path.dirname(__file__), 
                'multi_route_schema.sql'
            )
            
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(schema_sql)
            
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            return False
    
    # ========================================
    # Multi-Route Schedule Operations
    # ========================================
    
    def save_multi_route_schedule(self, schedule_data: Dict) -> str:
        """Save a multi-route schedule to database"""
        try:
            query = """
            INSERT INTO multi_route_schedules (
                schedule_id, num_trains, total_days, cargo_requirements,
                daily_actions, train_assignments, performance_metrics,
                cost_breakdown_zmw, efficiency_analysis
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            params = (
                schedule_data['schedule_id'],
                schedule_data['num_trains'],
                schedule_data['total_days'],
                json.dumps(schedule_data['cargo_requirements']),
                json.dumps(schedule_data['daily_actions']),
                json.dumps(schedule_data['train_assignments']),
                json.dumps(schedule_data['performance_metrics']),
                json.dumps(schedule_data['cost_breakdown_zmw']),
                json.dumps(schedule_data['efficiency_analysis'])
            )
            
            schedule_id = self.execute_insert(query, params)
            
            self._save_train_operations(schedule_id, schedule_data['train_assignments'])
            self._save_route_performance(schedule_id, schedule_data)
            self._save_performance_history(schedule_id, schedule_data)
            
            logger.info(f"Multi-route schedule {schedule_data['schedule_id']} saved successfully")
            return str(schedule_id)
            
        except Exception as e:
            logger.error(f"Error saving multi-route schedule: {e}")
            raise
    
    def _save_train_operations(self, schedule_id: str, train_assignments: List[Dict]):
        """Save detailed train operations"""
        try:
            query = """
            INSERT INTO train_operations (
                schedule_id, train_id, day, action, route_name,
                train_state, time_left, cargo_carried
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for assignment in train_assignments:
                        cursor.execute(query, (
                            schedule_id,
                            assignment['train_id'],
                            assignment['day'],
                            assignment['action'],
                            assignment.get('route_name'),
                            assignment.get('train_state'),
                            assignment.get('time_left'),
                            assignment.get('cargo_carried')
                        ))
        except Exception as e:
            logger.error(f"Error saving train operations: {e}")
            raise
    
    def _save_route_performance(self, schedule_id: str, schedule_data: Dict):
        """Save route-specific performance metrics"""
        try:
            query = """
            INSERT INTO route_performance (
                schedule_id, route_name, cargo_delivered, trains_assigned,
                efficiency_score, revenue_zmw
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            efficiency = schedule_data['efficiency_analysis']
            cost_breakdown = schedule_data['cost_breakdown_zmw']
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for route_name, route_eff in efficiency.get('route_efficiency', {}).items():
                        cursor.execute(query, (
                            schedule_id,
                            route_name,
                            schedule_data['performance_metrics']['total_cargo_delivered'] / max(1, len(efficiency.get('route_efficiency', {}))),
                            schedule_data['performance_metrics'].get('trains_used', 1),
                            route_eff,
                            cost_breakdown['revenue_zmw'] / max(1, len(efficiency.get('route_efficiency', {})))
                        ))
        except Exception as e:
            logger.error(f"Error saving route performance: {e}")
            raise
    
    def _save_performance_history(self, schedule_id: str, schedule_data: Dict):
        """Save performance metrics to history"""
        try:
            query = """
            INSERT INTO performance_history (
                schedule_id, metric_date, total_cargo_delivered,
                trains_used, efficiency, net_profit_zmw, coordination_bonus_zmw
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                schedule_id,
                date.today(),
                schedule_data['performance_metrics']['total_cargo_delivered'],
                schedule_data['performance_metrics'].get('trains_used', 1),
                schedule_data['performance_metrics'].get('efficiency', 0),
                schedule_data['cost_breakdown_zmw']['net_profit_zmw'],
                schedule_data['cost_breakdown_zmw'].get('coordination_bonus_zmw', 0)
            )
            
            self.execute_insert(query, params)
        except Exception as e:
            logger.error(f"Error saving performance history: {e}")
            raise
    
    def get_multi_route_schedule(self, schedule_id: str) -> Optional[Dict]:
        """Retrieve a multi-route schedule by ID"""
        try:
            query = """
            SELECT * FROM multi_route_schedules 
            WHERE schedule_id = %s AND status = 'active'
            """
            
            results = self.execute_query(query, (schedule_id,))
            
            if results:
                schedule = results[0]
                schedule['cargo_requirements'] = json.loads(schedule['cargo_requirements'])
                schedule['daily_actions'] = json.loads(schedule['daily_actions'])
                schedule['train_assignments'] = json.loads(schedule['train_assignments'])
                schedule['performance_metrics'] = json.loads(schedule['performance_metrics'])
                schedule['cost_breakdown_zmw'] = json.loads(schedule['cost_breakdown_zmw'])
                schedule['efficiency_analysis'] = json.loads(schedule['efficiency_analysis'])
                return schedule
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving multi-route schedule: {e}")
            raise
    
    def get_schedule_list(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get list of multi-route schedules"""
        try:
            query = """
            SELECT schedule_id, timestamp, num_trains, total_days,
                   (performance_metrics->>'total_cargo_delivered')::DECIMAL as total_cargo,
                   (performance_metrics->>'efficiency')::DECIMAL as efficiency,
                   (cost_breakdown_zmw->>'net_profit_zmw')::DECIMAL as net_profit_zmw,
                   status
            FROM multi_route_schedules
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
            """
            
            return self.execute_query(query, (limit, offset))
        except Exception as e:
            logger.error(f"Error retrieving schedule list: {e}")
            raise
    
    # ========================================
    # Performance Analytics Operations
    # ========================================
    
    def get_performance_trends(self, days: int = 30) -> List[Dict]:
        """Get performance trends for the last N days"""
        try:
            query = f"""
            SELECT 
                metric_date,
                SUM(total_cargo_delivered) as total_cargo,
                AVG(trains_used) as avg_trains,
                AVG(efficiency) as avg_efficiency,
                SUM(net_profit_zmw) as total_profit
            FROM performance_history 
            WHERE metric_date >= CURRENT_DATE - INTERVAL '{days} days'
            GROUP BY metric_date
            ORDER BY metric_date ASC
            """
            
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error retrieving performance trends: {e}")
            raise
    
    def get_route_performance_summary(self) -> List[Dict]:
        """Get route efficiency summary for charts"""
        try:
            query = """
                SELECT 
                    route_name,
                    AVG(efficiency) as avg_efficiency,
                    AVG(total_cargo_delivered) as avg_cargo,
                    SUM(total_cargo_delivered) as total_cargo,
                    AVG(trains_used) as avg_utilization,
                    COUNT(*) as schedule_count
                FROM performance_history 
                WHERE schedule_id IS NOT NULL AND route_name IS NOT NULL
                GROUP BY route_name
                ORDER BY avg_efficiency DESC
            """
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error retrieving route performance summary: {e}")
            raise
    
    def get_route_efficiency_summary(self) -> List[Dict]:
        """Get route efficiency summary (alias for get_route_performance_summary)"""
        return self.get_route_performance_summary()
    
    def get_performance_comparison(self, schedule_id: str) -> Optional[Dict]:
        """Get performance comparison data"""
        try:
            query = """
            SELECT * FROM schedule_comparisons 
            WHERE multi_route_schedule_id = %s
            """
            
            results = self.execute_query(query, (schedule_id,))
            
            if results:
                comparison = results[0]
                comparison['baseline_metrics'] = json.loads(comparison['baseline_metrics'])
                comparison['multi_route_metrics'] = json.loads(comparison['multi_route_metrics'])
                comparison['improvement_metrics'] = json.loads(comparison['improvement_metrics'])
                comparison['cargo_requirements'] = json.loads(comparison['cargo_requirements'])
                return comparison
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving performance comparison: {e}")
            raise
    
    # ========================================
    # Audit and Logging Operations
    # ========================================
    
    def log_audit_event(self, schedule_id: str, action_type: str, 
                       action_details: Dict, user_id: str = None, 
                       severity: str = 'INFO'):
        """Log an audit event"""
        try:
            query = """
            INSERT INTO multi_route_audit_logs (
                schedule_id, action_type, action_details, user_id, severity
            ) VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (
                schedule_id,
                action_type,
                json.dumps(action_details),
                user_id,
                severity
            )
            
            self.execute_insert(query, params)
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            raise
    
    def get_audit_logs(self, schedule_id: str = None, limit: int = 100) -> List[Dict]:
        """Get audit logs"""
        try:
            if schedule_id:
                query = """
                SELECT * FROM multi_route_audit_logs 
                WHERE schedule_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
                """
                params = (schedule_id, limit)
            else:
                query = """
                SELECT * FROM multi_route_audit_logs 
                ORDER BY timestamp DESC
                LIMIT %s
                """
                params = (limit,)
            
            results = self.execute_query(query, params)
            
            for result in results:
                if result['action_details']:
                    result['action_details'] = json.loads(result['action_details'])
            
            return results
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}")
            raise
    
    # ========================================
    # Statistics and Reporting Operations
    # ========================================
    
    def get_dashboard_statistics(self) -> Dict:
        """Get comprehensive dashboard statistics"""
        try:
            stats = {}
            
            query = "SELECT COUNT(*) as total FROM multi_route_schedules WHERE status = 'active'"
            result = self.execute_query(query)
            stats['total_schedules'] = result[0]['total'] if result else 0
            
            query = """
            SELECT AVG((performance_metrics->>'efficiency')::DECIMAL) as avg_efficiency,
                   AVG((cost_breakdown_zmw->>'net_profit_zmw')::DECIMAL) as avg_profit
            FROM multi_route_schedules WHERE status = 'active'
            """
            result = self.execute_query(query)
            stats['average_efficiency'] = float(result[0]['avg_efficiency'] or 0) if result else 0
            stats['average_profit'] = float(result[0]['avg_profit'] or 0) if result else 0
            
            query = """
            SELECT SUM((performance_metrics->>'total_cargo_delivered')::DECIMAL) as total_cargo
            FROM multi_route_schedules WHERE status = 'active'
            """
            result = self.execute_query(query)
            stats['total_cargo_delivered'] = float(result[0]['total_cargo'] or 0) if result else 0
            
            query = """
            SELECT COUNT(*) as recent_schedules
            FROM multi_route_schedules 
            WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days' AND status = 'active'
            """
            result = self.execute_query(query)
            stats['recent_schedules'] = result[0]['recent_schedules'] if result else 0
            
            return stats
        except Exception as e:
            logger.error(f"Error retrieving dashboard statistics: {e}")
            raise
    
    def get_route_performance_chart_data(self, days: int = 30) -> List[Dict]:
        """Get route performance data for charts"""
        try:
            query = f"""
            SELECT route_name, metric_date, average_efficiency, total_cargo, avg_utilization
            FROM route_efficiency_trends
            WHERE metric_date >= CURRENT_DATE - INTERVAL '{days} days'
            ORDER BY route_name, metric_date
            """
            
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error retrieving route performance chart data: {e}")
            raise


# Global database manager instance
db_manager = DatabaseManager()