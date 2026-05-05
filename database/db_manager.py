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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and operations manager for multi-route system"""
    
    def __init__(self, db_url: str = None):
        """Initialize database connection"""
        self.db_url = db_url or os.getenv(
            'DATABASE_URL',
            'postgresql://tazara:tazara123@localhost:5432/tazara_multi_route'
        )
        self.connection = None
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        conn = psycopg2.connect(self.db_url)
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
                        # Handle cases where no results are returned (e.g. no RETURNING clause)
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
            
            # Save train operations
            self._save_train_operations(schedule_id, schedule_data['train_assignments'])
            
            # Save route performance
            self._save_route_performance(schedule_id, schedule_data)
            
            # Save performance history
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
                    for route_name, route_eff in efficiency['route_efficiency'].items():
                        cursor.execute(query, (
                            schedule_id,
                            route_name,
                            schedule_data['performance_metrics']['total_cargo_delivered'] / 3,  # Distribute equally
                            schedule_data['performance_metrics']['trains_used'],
                            route_eff,
                            cost_breakdown['revenue_zmw'] / 3  # Distribute equally
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
                schedule_data['performance_metrics']['trains_used'],
                schedule_data['performance_metrics']['efficiency'],
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
                # Convert JSON fields back to Python objects
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
            query = """
            SELECT 
                metric_date,
                SUM(total_cargo_delivered) as total_cargo,
                AVG(trains_used) as avg_trains,
                AVG(efficiency) as avg_efficiency,
                SUM(net_profit_zmw) as total_profit
            FROM performance_history 
            WHERE metric_date >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY metric_date
            ORDER BY metric_date ASC
            """ % days
            
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
                WHERE schedule_id IS NOT NULL
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
            
            # Convert action_details from JSON
            for result in results:
                if result['action_details']:
                    result['action_details'] = json.loads(result['action_details'])
            
            return results
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}")
            raise
    
    # ========================================
    # Configuration Operations
    # ========================================
    
    def get_system_config(self, config_key: str = None) -> Dict:
        """Get system configuration"""
        try:
            if config_key:
                query = "SELECT * FROM system_configuration WHERE config_key = %s AND is_active = TRUE"
                results = self.execute_query(query, (config_key,))
                if results:
                    return json.loads(results[0]['config_value'])
                return {}
            else:
                query = "SELECT config_key, config_value FROM system_configuration WHERE is_active = TRUE"
                results = self.execute_query(query)
                return {row['config_key']: json.loads(row['config_value']) for row in results}
        except Exception as e:
            logger.error(f"Error retrieving system configuration: {e}")
            raise
    
    def update_system_config(self, config_key: str, config_value: Dict):
        """Update system configuration"""
        try:
            query = """
                UPDATE system_configuration 
                SET config_value = %s, updated_at = NOW()
                WHERE config_key = %s
            """
            
            # Convert config_value to JSON string
            import json
            config_json = json.dumps(config_value)
            
            params = (config_json, config_key)
            self.execute_insert(query, params)
            
            logger.info(f"Updated configuration {config_key}: {config_value}")
            
        except Exception as e:
            logger.error(f"Error updating system configuration: {e}")
            raise
    
    # ========================================
    # Statistics and Reporting Operations
    # ========================================
    
    def get_dashboard_statistics(self) -> Dict:
        """Get comprehensive dashboard statistics"""
        try:
            stats = {}
            
            # Total schedules
            query = "SELECT COUNT(*) as total FROM multi_route_schedules WHERE status = 'active'"
            result = self.execute_query(query)
            stats['total_schedules'] = result[0]['total']
            
            # Average performance
            query = """
            SELECT AVG((performance_metrics->>'efficiency')::DECIMAL) as avg_efficiency,
                   AVG((cost_breakdown_zmw->>'net_profit_zmw')::DECIMAL) as avg_profit
            FROM multi_route_schedules WHERE status = 'active'
            """
            result = self.execute_query(query)
            stats['average_efficiency'] = float(result[0]['avg_efficiency'] or 0)
            stats['average_profit'] = float(result[0]['avg_profit'] or 0)
            
            # Total cargo delivered
            query = """
            SELECT SUM((performance_metrics->>'total_cargo_delivered')::DECIMAL) as total_cargo
            FROM multi_route_schedules WHERE status = 'active'
            """
            result = self.execute_query(query)
            stats['total_cargo_delivered'] = float(result[0]['total_cargo'] or 0)
            
            # Recent activity
            query = """
            SELECT COUNT(*) as recent_schedules
            FROM multi_route_schedules 
            WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days' AND status = 'active'
            """
            result = self.execute_query(query)
            stats['recent_schedules'] = result[0]['recent_schedules']
            
            return stats
        except Exception as e:
            logger.error(f"Error retrieving dashboard statistics: {e}")
            raise
    
    def get_route_performance_chart_data(self, days: int = 30) -> List[Dict]:
        """Get route performance data for charts"""
        try:
            query = """
            SELECT route_name, metric_date, average_efficiency, total_cargo, avg_utilization
            FROM route_efficiency_trends
            WHERE metric_date >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY route_name, metric_date
            """ % days
            
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error retrieving route performance chart data: {e}")
            raise

# Global database manager instance
db_manager = DatabaseManager()

# ==============================
    # LABOR OPTIMIZATION METHODS
    # ==============================

def save_labor_cost_record(self, labor_cost_data: Dict) -> str:
        """Save labor cost record to database"""
        try:
            query = """
                INSERT INTO labor_costs (
                    schedule_id, driver_id, train_id, route_name, work_date,
                    regular_hours, overtime_hours, premium_overtime_hours, total_hours,
                    base_hourly_rate, regular_cost_zmw, overtime_cost_zmw,
                    premium_overtime_cost_zmw, total_labor_cost_zmw,
                    skill_level, shift_type, is_weekend, route_complexity_factor, efficiency_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            params = (
                labor_cost_data['schedule_id'],
                labor_cost_data['driver_id'],
                labor_cost_data.get('train_id'),
                labor_cost_data.get('route_name'),
                labor_cost_data.get('work_date', date.today()),
                labor_cost_data['regular_hours'],
                labor_cost_data['overtime_hours'],
                labor_cost_data['premium_overtime_hours'],
                labor_cost_data['total_hours'],
                labor_cost_data['base_hourly_rate'],
                labor_cost_data['regular_cost_zmw'],
                labor_cost_data['overtime_cost_zmw'],
                labor_cost_data['premium_overtime_cost_zmw'],
                labor_cost_data['total_labor_cost_zmw'],
                labor_cost_data['skill_level'],
                labor_cost_data['shift_type'],
                labor_cost_data['is_weekend'],
                labor_cost_data.get('route_complexity_factor', 1.0),
                labor_cost_data.get('efficiency_score', 0.0)
            )
            
            return self.execute_insert(query, params)
            
        except Exception as e:
            logger.error(f"Error saving labor cost record: {e}")
            raise

def save_optimization_event(self, event_data: Dict) -> str:
        """Save optimization event to database"""
        try:
            query = """
                INSERT INTO optimization_events (
                    event_type, schedule_id, event_description,
                    old_assignment, new_assignment, cost_savings_zmw,
                    efficiency_improvement, overtime_reduction_hours,
                    processing_time_ms, algorithm_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            params = (
                event_data['event_type'],
                event_data['schedule_id'],
                event_data.get('event_description'),
                json.dumps(event_data.get('old_assignment', {})),
                json.dumps(event_data.get('new_assignment', {})),
                event_data.get('cost_savings_zmw', 0.0),
                event_data.get('efficiency_improvement', 0.0),
                event_data.get('overtime_reduction_hours', 0.0),
                event_data.get('processing_time_ms', 0),
                event_data.get('algorithm_version', 'v1.0')
            )
            
            return self.execute_insert(query, params)
            
        except Exception as e:
            logger.error(f"Error saving optimization event: {e}")
            raise

def update_labor_performance_trends(self, trend_data: Dict) -> bool:
        """Update labor performance trends"""
        try:
            query = """
                INSERT INTO labor_performance_trends (
                    metric_date, route_name, total_drivers_worked, total_hours_worked,
                    total_overtime_hours, total_labor_cost_zmw, average_efficiency_score,
                    average_cost_per_hour, overtime_percentage, cost_trend_percentage,
                    efficiency_trend_percentage
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (metric_date, route_name) 
                DO UPDATE SET 
                    total_drivers_worked = EXCLUDED.total_drivers_worked,
                    total_hours_worked = EXCLUDED.total_hours_worked,
                    total_overtime_hours = EXCLUDED.total_overtime_hours,
                    total_labor_cost_zmw = EXCLUDED.total_labor_cost_zmw,
                    average_efficiency_score = EXCLUDED.average_efficiency_score,
                    average_cost_per_hour = EXCLUDED.average_cost_per_hour,
                    overtime_percentage = EXCLUDED.overtime_percentage,
                    cost_trend_percentage = EXCLUDED.cost_trend_percentage,
                    efficiency_trend_percentage = EXCLUDED.efficiency_trend_percentage
            """
            
            params = (
                trend_data.get('metric_date', date.today()),
                trend_data.get('route_name'),
                trend_data.get('total_drivers_worked', 0),
                trend_data.get('total_hours_worked', 0.0),
                trend_data.get('total_overtime_hours', 0.0),
                trend_data.get('total_labor_cost_zmw', 0.0),
                trend_data.get('average_efficiency_score', 0.0),
                trend_data.get('average_cost_per_hour', 0.0),
                trend_data.get('overtime_percentage', 0.0),
                trend_data.get('cost_trend_percentage', 0.0),
                trend_data.get('efficiency_trend_percentage', 0.0)
            )
            
            self.execute_insert(query, params)
            return True
            
        except Exception as e:
            logger.error(f"Error updating labor performance trends: {e}")
            return False

# Add methods to DatabaseManager class
DatabaseManager.save_labor_cost_record = save_labor_cost_record
DatabaseManager.save_optimization_event = save_optimization_event
DatabaseManager.update_labor_performance_trends = update_labor_performance_trends

# ==============================
# PHASE 4: SKILL MANAGEMENT METHODS
# ==============================

def save_driver_skill(self, skill_data: Dict) -> str:
    """Save or update driver skill record"""
    try:
        query = """
            INSERT INTO driver_skills (
                driver_id, driver_name, skill_category, skill_level, years_experience,
                locomotive_types, route_expertise, certifications,
                efficiency_score, safety_score, reliability_score,
                preferred_shifts, max_overtime_hours, current_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (driver_id) DO UPDATE SET
                driver_name = EXCLUDED.driver_name,
                skill_category = EXCLUDED.skill_category,
                skill_level = EXCLUDED.skill_level,
                years_experience = EXCLUDED.years_experience,
                locomotive_types = EXCLUDED.locomotive_types,
                route_expertise = EXCLUDED.route_expertise,
                certifications = EXCLUDED.certifications,
                efficiency_score = EXCLUDED.efficiency_score,
                safety_score = EXCLUDED.safety_score,
                reliability_score = EXCLUDED.reliability_score,
                preferred_shifts = EXCLUDED.preferred_shifts,
                max_overtime_hours = EXCLUDED.max_overtime_hours,
                current_status = EXCLUDED.current_status,
                last_updated = CURRENT_TIMESTAMP
            RETURNING id
        """
        params = (
            skill_data['driver_id'],
            skill_data['driver_name'],
            skill_data.get('skill_category', 'locomotive'),
            skill_data.get('skill_level', 3),
            skill_data.get('years_experience', 0),
            json.dumps(skill_data.get('locomotive_types', [])),
            json.dumps(skill_data.get('route_expertise', [])),
            json.dumps(skill_data.get('certifications', [])),
            skill_data.get('efficiency_score', 70.0),
            skill_data.get('safety_score', 95.0),
            skill_data.get('reliability_score', 90.0),
            json.dumps(skill_data.get('preferred_shifts', ['day'])),
            skill_data.get('max_overtime_hours', 4.0),
            skill_data.get('current_status', 'available')
        )
        return self.execute_insert(query, params)
    except Exception as e:
        logger.error(f"Error saving driver skill: {e}")
        raise


def get_driver_skills(self, driver_id: str = None, skill_category: str = None, 
                     min_skill_level: int = None, route: str = None) -> List[Dict]:
    """Query driver skills with optional filters"""
    try:
        conditions = []
        params = []
        
        if driver_id:
            conditions.append("driver_id = %s")
            params.append(driver_id)
        if skill_category:
            conditions.append("skill_category = %s")
            params.append(skill_category)
        if min_skill_level:
            conditions.append("skill_level >= %s")
            params.append(min_skill_level)
        if route:
            conditions.append("route_expertise @> %s")
            params.append(json.dumps([route]))
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        query = f"""
            SELECT * FROM driver_skills
            WHERE {where_clause}
            ORDER BY skill_level DESC, efficiency_score DESC
        """
        return self.execute_query(query, tuple(params))
    except Exception as e:
        logger.error(f"Error querying driver skills: {e}")
        raise


def find_matching_drivers(self, required_skills: List[str], route: str = None,
                         min_efficiency: float = 70.0, shift_type: str = None) -> List[Dict]:
    """Find drivers matching specific skill requirements"""
    try:
        query = """
            SELECT *, 
                (
                    (skill_level * 20) + 
                    (efficiency_score * 0.3) + 
                    (safety_score * 0.2) +
                    CASE WHEN route_expertise @> %s THEN 20 ELSE 0 END
                ) as match_score
            FROM driver_skills
            WHERE skill_category = ANY(%s)
            AND efficiency_score >= %s
            AND current_status = 'available'
            AND %s = ANY(preferred_shifts)
            ORDER BY match_score DESC
        """
        params = (
            json.dumps([route] if route else []),
            required_skills,
            min_efficiency,
            shift_type or 'day'
        )
        return self.execute_query(query, params)
    except Exception as e:
        logger.error(f"Error finding matching drivers: {e}")
        raise


def save_skill_task_match(self, match_data: Dict) -> str:
    """Record a skill-task matching event"""
    try:
        query = """
            INSERT INTO skill_task_matching (
                task_id, task_type, driver_id, route, required_skills,
                matched_skills, skill_match_score, assigned_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            match_data['task_id'],
            match_data['task_type'],
            match_data['driver_id'],
            match_data.get('route'),
            json.dumps(match_data.get('required_skills', [])),
            json.dumps(match_data.get('matched_skills', [])),
            match_data.get('skill_match_score', 0.0),
            match_data.get('assigned_date', datetime.utcnow())
        )
        return self.execute_insert(query, params)
    except Exception as e:
        logger.error(f"Error saving skill task match: {e}")
        raise


# ==============================
# PHASE 4: GEOGRAPHIC CLUSTERING METHODS
# ==============================

def save_geographic_cluster(self, cluster_data: Dict) -> str:
    """Save or update geographic cluster"""
    try:
        query = """
            INSERT INTO geographic_clusters (
                cluster_id, cluster_name, center_lat, center_lng, radius_km,
                covered_routes, fuel_efficiency_factor, avg_travel_time_reduction,
                peak_hours, congestion_factor
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (cluster_id) DO UPDATE SET
                cluster_name = EXCLUDED.cluster_name,
                center_lat = EXCLUDED.center_lat,
                center_lng = EXCLUDED.center_lng,
                radius_km = EXCLUDED.radius_km,
                covered_routes = EXCLUDED.covered_routes,
                fuel_efficiency_factor = EXCLUDED.fuel_efficiency_factor,
                avg_travel_time_reduction = EXCLUDED.avg_travel_time_reduction,
                peak_hours = EXCLUDED.peak_hours,
                congestion_factor = EXCLUDED.congestion_factor,
                last_updated = CURRENT_TIMESTAMP
            RETURNING id
        """
        params = (
            cluster_data['cluster_id'],
            cluster_data['cluster_name'],
            cluster_data['center_lat'],
            cluster_data['center_lng'],
            cluster_data.get('radius_km', 50.0),
            json.dumps(cluster_data.get('covered_routes', [])),
            cluster_data.get('fuel_efficiency_factor', 1.0),
            cluster_data.get('avg_travel_time_reduction', 0.0),
            json.dumps(cluster_data.get('peak_hours', [])),
            cluster_data.get('congestion_factor', 1.0)
        )
        return self.execute_insert(query, params)
    except Exception as e:
        logger.error(f"Error saving geographic cluster: {e}")
        raise


def get_optimal_clusters(self, route: str = None, min_efficiency: float = None) -> List[Dict]:
    """Get geographic clusters optimized for specific criteria"""
    try:
        conditions = ["is_active = TRUE"]
        params = []
        
        if route:
            conditions.append("covered_routes @> %s")
            params.append(json.dumps([route]))
        if min_efficiency:
            conditions.append("fuel_efficiency_factor <= %s")
            params.append(min_efficiency)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT * FROM geographic_clusters
            WHERE {where_clause}
            ORDER BY fuel_efficiency_factor ASC, avg_travel_time_reduction DESC
        """
        return self.execute_query(query, tuple(params))
    except Exception as e:
        logger.error(f"Error getting optimal clusters: {e}")
        raise


def get_route_segments(self, route: str = None, cluster_id: str = None) -> List[Dict]:
    """Get route segments with optimization data"""
    try:
        conditions = []
        params = []
        
        if route:
            conditions.append("route = %s")
            params.append(route)
        if cluster_id:
            conditions.append("cluster_id = %s")
            params.append(cluster_id)
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        query = f"""
            SELECT * FROM route_segments
            WHERE {where_clause}
            ORDER BY route, distance_km
        """
        return self.execute_query(query, tuple(params))
    except Exception as e:
        logger.error(f"Error getting route segments: {e}")
        raise


# ==============================
# PHASE 4: ASSET MANAGEMENT METHODS
# ==============================

def save_asset_assignment(self, assignment_data: Dict) -> str:
    """Save asset assignment record"""
    try:
        query = """
            INSERT INTO asset_assignments (
                asset_id, asset_type, asset_name, schedule_id, driver_id, route,
                assignment_start, planned_utilization_hours, operating_cost_zmw
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            assignment_data['asset_id'],
            assignment_data['asset_type'],
            assignment_data['asset_name'],
            assignment_data.get('schedule_id'),
            assignment_data.get('driver_id'),
            assignment_data.get('route'),
            assignment_data.get('assignment_start', datetime.utcnow()),
            assignment_data.get('planned_utilization_hours', 0.0),
            assignment_data.get('operating_cost_zmw', 0.0)
        )
        return self.execute_insert(query, params)
    except Exception as e:
        logger.error(f"Error saving asset assignment: {e}")
        raise


def get_asset_utilization(self, asset_id: str = None, asset_type: str = None,
                         start_date: date = None, end_date: date = None) -> List[Dict]:
    """Get asset utilization data with time range filtering"""
    try:
        conditions = []
        params = []
        
        if asset_id:
            conditions.append("asset_id = %s")
            params.append(asset_id)
        if asset_type:
            conditions.append("asset_type = %s")
            params.append(asset_type)
        if start_date:
            conditions.append("metric_date >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("metric_date <= %s")
            params.append(end_date)
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        query = f"""
            SELECT asset_id, asset_type, 
                   AVG(utilization_rate) as avg_utilization,
                   SUM(cargo_volume_tons) as total_cargo,
                   SUM(trips_completed) as total_trips,
                   AVG(operating_cost_zmw) as avg_daily_cost
            FROM asset_utilization_daily
            WHERE {where_clause}
            GROUP BY asset_id, asset_type
            ORDER BY avg_utilization DESC
        """
        return self.execute_query(query, tuple(params))
    except Exception as e:
        logger.error(f"Error getting asset utilization: {e}")
        raise


def save_resource_conflict(self, conflict_data: Dict) -> str:
    """Record a resource conflict"""
    try:
        query = """
            INSERT INTO resource_conflicts (
                conflict_id, conflict_type, resource_type, resource_id,
                primary_assignment_id, conflicting_assignment_id,
                overlap_start, overlap_end, overlap_duration_minutes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            conflict_data['conflict_id'],
            conflict_data['conflict_type'],
            conflict_data['resource_type'],
            conflict_data['resource_id'],
            conflict_data['primary_assignment_id'],
            conflict_data['conflicting_assignment_id'],
            conflict_data['overlap_start'],
            conflict_data['overlap_end'],
            conflict_data['overlap_duration_minutes']
        )
        return self.execute_insert(query, params)
    except Exception as e:
        logger.error(f"Error saving resource conflict: {e}")
        raise


def get_resource_conflicts(self, status: str = 'open', resource_type: str = None) -> List[Dict]:
    """Get resource conflicts with optional filtering"""
    try:
        conditions = ["status = %s"]
        params = [status]
        
        if resource_type:
            conditions.append("resource_type = %s")
            params.append(resource_type)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT * FROM resource_conflicts
            WHERE {where_clause}
            ORDER BY detected_at DESC
        """
        return self.execute_query(query, tuple(params))
    except Exception as e:
        logger.error(f"Error getting resource conflicts: {e}")
        raise


# ==============================
# PHASE 4: OPTIMIZATION RECOMMENDATIONS
# ==============================

def save_optimization_recommendation(self, recommendation_data: Dict) -> str:
    """Save AI-generated optimization recommendation"""
    try:
        query = """
            INSERT INTO optimization_recommendations (
                recommendation_id, recommendation_type, target_resource_type, target_resource_id,
                current_state, recommended_state, expected_improvement,
                confidence_score, reasoning, factors_considered, priority, expires_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            recommendation_data['recommendation_id'],
            recommendation_data['recommendation_type'],
            recommendation_data['target_resource_type'],
            recommendation_data['target_resource_id'],
            json.dumps(recommendation_data['current_state']),
            json.dumps(recommendation_data['recommended_state']),
            json.dumps(recommendation_data.get('expected_improvement', {})),
            recommendation_data['confidence_score'],
            recommendation_data.get('reasoning', ''),
            json.dumps(recommendation_data.get('factors_considered', {})),
            recommendation_data.get('priority', 'medium'),
            recommendation_data.get('expires_at')
        )
        return self.execute_insert(query, params)
    except Exception as e:
        logger.error(f"Error saving optimization recommendation: {e}")
        raise


def get_optimization_recommendations(self, status: str = 'pending', 
                                   priority: str = None, limit: int = 10) -> List[Dict]:
    """Get optimization recommendations with filtering"""
    try:
        conditions = ["status = %s"]
        params = [status]
        
        if priority:
            conditions.append("priority = %s")
            params.append(priority)
        
        if status == 'pending':
            conditions.append("(expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)")
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT * FROM optimization_recommendations
            WHERE {where_clause}
            ORDER BY 
                CASE priority 
                    WHEN 'critical' THEN 1 
                    WHEN 'high' THEN 2 
                    WHEN 'medium' THEN 3 
                    ELSE 4 
                END,
                confidence_score DESC
            LIMIT %s
        """
        params.append(limit)
        
        return self.execute_query(query, tuple(params))
    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {e}")
        raise


# Add Phase 4 methods to DatabaseManager
DatabaseManager.save_driver_skill = save_driver_skill
DatabaseManager.get_driver_skills = get_driver_skills
DatabaseManager.find_matching_drivers = find_matching_drivers
DatabaseManager.save_skill_task_match = save_skill_task_match
DatabaseManager.save_geographic_cluster = save_geographic_cluster
DatabaseManager.get_optimal_clusters = get_optimal_clusters
DatabaseManager.get_route_segments = get_route_segments
DatabaseManager.save_asset_assignment = save_asset_assignment
DatabaseManager.get_asset_utilization = get_asset_utilization
DatabaseManager.save_resource_conflict = save_resource_conflict
DatabaseManager.get_resource_conflicts = get_resource_conflicts
DatabaseManager.save_optimization_recommendation = save_optimization_recommendation
DatabaseManager.get_optimization_recommendations = get_optimization_recommendations
