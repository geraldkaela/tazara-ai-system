"""
Priority Auto-Scheduler API Routes - Fixed Version
AI-powered automatic scheduling based on priority queue
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, timedelta

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'tazara_multi_route',
    'user': 'tazara',
    'password': 'tazara123'
}

router = APIRouter(tags=["Priority Auto-Scheduler"])

class AutoScheduleRequest(BaseModel):
    """Request for automatic priority-based scheduling"""
    num_trains: int = 5
    max_days: int = 7
    include_all_pending: bool = True
    max_orders: Optional[int] = None  # Optional limit on number of orders to schedule

class AutoScheduleResponse(BaseModel):
    """Response from auto-scheduling"""
    success: bool
    schedule_id: Optional[str] = None
    orders_scheduled: int = 0
    total_cargo_tons: float = 0
    priority_summary: Dict = {}
    schedule_details: Optional[Dict] = None
    message: str

def calculate_priority_score(order):
    """Calculate priority score for an order"""
    score = 0
    urgency_level = "normal"
    
    # Base score from priority_level (1=highest, 5=lowest)
    priority_level = order.get('priority_level', 3)
    if priority_level == 1:
        score += 40
        urgency_level = "emergency"
    elif priority_level == 2:
        score += 30
        urgency_level = "urgent"
    elif priority_level == 3:
        score += 20
        urgency_level = "priority"
    elif priority_level == 4:
        score += 10
    else:
        score += 5
    
    # Deadline urgency
    deadline = order.get('requested_arrival_date')
    if deadline:
        try:
            if isinstance(deadline, str):
                deadline_date = datetime.fromisoformat(deadline)
            else:
                deadline_date = datetime.combine(deadline, datetime.min.time())
            
            days_until_deadline = (deadline_date - datetime.now()).days
            
            if days_until_deadline <= 1:
                score += 30
                urgency_level = "emergency"
            elif days_until_deadline <= 3:
                score += 20
                urgency_level = "urgent"
            elif days_until_deadline <= 7:
                score += 10
                urgency_level = "priority"
        except:
            pass
    
    # Cargo weight bonus (larger shipments get priority)
    cargo_weight = order.get('cargo_weight', 0)
    if cargo_weight > 1000:
        score += 10
    elif cargo_weight > 500:
        score += 5
    elif cargo_weight > 200:
        score += 3
    
    # Special cargo types
    cargo_type = order.get('cargo_type', '').lower()
    if any(keyword in cargo_type for keyword in ['medical', 'emergency', 'urgent', 'perishable']):
        score += 15
        urgency_level = "emergency"
    elif any(keyword in cargo_type for keyword in ['copper', 'minerals', 'coal', 'fuel']):
        score += 10
    elif any(keyword in cargo_type for keyword in ['manufactured', 'machinery']):
        score += 5
    
    # Route distance bonus (longer routes get priority)
    origin = order.get('origin_station', '').lower()
    dest = order.get('destination_station', '').lower()
    
    # Check for full TAZARA route (both directions)
    if ('dar es salaam' in origin and 'kapiri' in dest) or ('kapiri' in origin and 'dar es salaam' in dest):
        score += 10
    elif 'dar es salaam' in origin or 'kapiri' in dest or 'mbeya' in origin or 'mbeya' in dest:
        score += 5
    
    # Customer name recognition (repeat customers get bonus)
    customer_name = order.get('customer_name', '').lower()
    if any(keyword in customer_name for keyword in ['government', 'ministry', 'corporation', 'ltd']):
        score += 5
    
    return min(score, 100)

def save_schedule_to_database(schedule_data):
    """Save schedule to database - Fixed version"""
    try:
        print(f"DEBUG: Attempting to save schedule: {schedule_data['schedule_id']}")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Insert schedule
        insert_query = """
        INSERT INTO schedules (
            schedule_id, created_at, num_trains, max_days, 
            total_cargo_delivered, efficiency_score, total_reward,
            schedule_data, metadata
        ) VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            schedule_data['schedule_id'],
            schedule_data['num_trains'],
            schedule_data['max_days'],
            float(schedule_data['performance_metrics']['total_cargo_delivered']),
            float(schedule_data['performance_metrics']['efficiency_score']),
            float(schedule_data['performance_metrics']['total_reward']),
            json.dumps(schedule_data),
            json.dumps(schedule_data['priority_metadata'])
        ))
        
        # Insert daily assignments
        for day_assignment in schedule_data['daily_assignments']:
            for assignment in day_assignment['assignments']:
                insert_query = """
                INSERT INTO daily_assignments (
                    schedule_id, day, train_id, route, cargo_tons, action
                ) VALUES (%s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_query, (
                    schedule_data['schedule_id'],
                    day_assignment['day'],
                    assignment['train_id'],
                    assignment['route'],
                    assignment['cargo_tons'],
                    assignment['action']
                ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"ERROR saving schedule: {e}")
        return False

@router.post("/auto-schedule", response_model=AutoScheduleResponse)
async def create_auto_schedule(request: AutoScheduleRequest):
    """Create automatic schedule based on priority queue"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get pending orders and calculate priority scores
        orders_query = """
        SELECT 
            order_id,
            customer_name,
            cargo_type,
            cargo_weight,
            origin_station,
            destination_station,
            priority_level,
            requested_departure_date,
            requested_arrival_date,
            created_at,
            status
        FROM customer_orders
        WHERE status IN ('pending', 'confirmed')
        AND created_at >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY created_at DESC
        """
        
        if request.max_orders:
            orders_query += f" LIMIT {request.max_orders}"
        
        cursor.execute(orders_query)
        orders = [dict(row) for row in cursor.fetchall()]
        
        if not orders:
            cursor.close()
            conn.close()
            return AutoScheduleResponse(
                success=False,
                message="No pending orders found for scheduling"
            )
        
        # Calculate priority scores and sort
        scored_orders = []
        for order in orders:
            score = calculate_priority_score(order)
            order['priority_score'] = score
            scored_orders.append(order)
        
        # Sort by priority score (highest first)
        scored_orders.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Group orders by route for scheduling
        route_groups = {}
        total_cargo = 0
        priority_summary = {
            'emergency': 0,
            'urgent': 0,
            'priority': 0,
            'normal': 0
        }
        
        for order in scored_orders:
            route_key = f"{order['origin_station']}_TO_{order['destination_station']}"
            if route_key not in route_groups:
                route_groups[route_key] = []
            route_groups[route_key].append(order)
            total_cargo += order['cargo_weight']
            
            # Count priority levels
            if order['priority_score'] >= 70:
                priority_summary['emergency'] += 1
            elif order['priority_score'] >= 50:
                priority_summary['urgent'] += 1
            elif order['priority_score'] >= 30:
                priority_summary['priority'] += 1
            else:
                priority_summary['normal'] += 1
        
        # Create simple schedule (bypass RL agent for now)
        schedule_id = f"AUTO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create daily assignments based on priority order
        daily_assignments = []
        day = 0
        
        # Assign trains to routes based on priority order
        for route_key, route_orders in route_groups.items():
            if route_orders and day < request.max_days:
                # Assign one train to this route
                train_id = (day % request.num_trains) + 1
                
                # Calculate total cargo for this route
                route_cargo = sum(order['cargo_weight'] for order in route_orders)
                
                daily_assignments.append({
                    'day': day + 1,
                    'assignments': [{
                        'train_id': f"Train_{train_id}",
                        'route': route_key.replace('_TO_', ' to '),
                        'cargo_tons': min(route_cargo, 1000),  # Max 1000 tons per train
                        'action': 'assigned'
                    }]
                })
                day += 1
        
        # Calculate performance metrics
        total_cargo_delivered = sum(
            float(assignment['cargo_tons']) 
            for day_assignment in daily_assignments 
            for assignment in day_assignment['assignments']
            if assignment['action'] == 'assigned'
        )
        
        performance_metrics = {
            'total_cargo_delivered': total_cargo_delivered,
            'total_reward': total_cargo_delivered * 10,  # Simple reward calculation
            'efficiency_score': total_cargo_delivered / (request.num_trains * request.max_days * 500),
            'days_completed': len(daily_assignments)
        }
        
        # Create schedule data
        schedule_data = {
            'schedule_id': schedule_id,
            'num_trains': request.num_trains,
            'max_days': request.max_days,
            'cargo_requirements': {route_key.replace('_TO_', '_'): float(sum(order['cargo_weight'] for order in route_orders)) for route_key, route_orders in route_groups.items()},
            'daily_actions': [],
            'daily_assignments': daily_assignments,
            'performance_metrics': performance_metrics,
            'cost_breakdown': {
                'fuel_cost': float(total_cargo_delivered * 50),
                'crew_cost': float(request.num_trains * request.max_days * 1000),
                'maintenance_cost': float(total_cargo_delivered * 20)
            },
            'efficiency_analysis': {
                'cargo_per_train_per_day': float(total_cargo_delivered / (request.num_trains * request.max_days)),
                'utilization_rate': float(performance_metrics['efficiency_score'] * 100),
                'total_efficiency': 'High' if performance_metrics['efficiency_score'] > 0.5 else 'Medium'
            },
            'priority_metadata': {
                'based_on_priority': True,
                'orders_count': len(scored_orders),
                'avg_priority_score': float(sum(order['priority_score'] for order in scored_orders) / len(scored_orders))
            }
        }
        
        # Save to database
        save_success = save_schedule_to_database(schedule_data)
        
        # Update order statuses to 'scheduled'
        if save_success:
            order_ids = [order['order_id'] for order in scored_orders]
            
            update_query = """
            UPDATE customer_orders 
            SET status = 'scheduled', 
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ANY(%s)
            """
            
            cursor.execute(update_query, (order_ids,))
            conn.commit()
        
        cursor.close()
        conn.close()
        
        if save_success:
            return AutoScheduleResponse(
                success=True,
                schedule_id=schedule_id,
                orders_scheduled=len(scored_orders),
                total_cargo_tons=total_cargo,
                priority_summary=priority_summary,
                schedule_details=schedule_data,
                message=f"Auto-schedule {schedule_id} created successfully with {total_cargo_delivered} tons delivered"
            )
        else:
            return AutoScheduleResponse(
                success=False,
                message="Failed to save schedule to database"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Auto-scheduling failed: {str(e)}"
        )

@router.get("/auto-schedule/status")
async def get_auto_schedule_status():
    """Get status of auto-scheduling system"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get statistics
        stats_query = """
        SELECT 
            COUNT(*) as total_orders,
            COUNT(CASE WHEN status = 'scheduled' THEN 1 END) as scheduled_orders,
            COUNT(CASE WHEN status IN ('pending', 'confirmed') THEN 1 END) as pending_orders,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
            SUM(CASE WHEN status = 'scheduled' THEN cargo_weight ELSE 0 END) as scheduled_cargo_tons
        FROM customer_orders
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        """
        
        cursor.execute(stats_query)
        stats = dict(cursor.fetchone())
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "total_orders": stats.get('total_orders', 0),
            "scheduled_orders": stats.get('scheduled_orders', 0),
            "pending_orders": stats.get('pending_orders', 0),
            "completed_orders": stats.get('completed_orders', 0),
            "scheduled_cargo_tons": float(stats.get('scheduled_cargo_tons', 0)),
            "auto_schedule_ready": stats.get('pending_orders', 0) > 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get auto-schedule status: {str(e)}"
        )
