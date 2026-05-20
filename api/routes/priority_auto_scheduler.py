"""
Priority Auto-Scheduler API Routes
AI-powered automatic scheduling based on priority queue
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta

import psycopg2
import re
from api.db_utils import get_db_connection
from psycopg2.extras import RealDictCursor

from api.config import DB_CONFIG
from api.auth.rbac import Permission, require_permission
from api.auth.auth import get_current_user, UserInDB
import json
from decimal import Decimal

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'tazara_multi_route',
    'user': 'tazara',
    'password': 'tazara123'
}

router = APIRouter(tags=["Priority Auto-Scheduler"])

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

class AutoScheduleRequest(BaseModel):
    """Request for automatic priority-based scheduling"""
    num_trains: int = 20
    max_days: int = 7
    include_all_pending: bool = True
    max_orders: Optional[int] = None  # Optional limit on number of orders to schedule


def get_train_capacities() -> Dict[int, int]:
    """Return the available TAZARA fleet capacities for auto-scheduling."""
    # Uniform operational assumption: every train can carry up to 1,300 tons.
    # This changes capacity calculations only; it does not change the scheduling
    # selection/assignment algorithm structure.
    return {train_id: 1300 for train_id in range(1, 21)}


def extract_train_number(train_id: str) -> Optional[int]:
    """Extract numeric train id from labels like Train_6, Train_6_2, T-06."""
    if not train_id:
        return None
    match = re.search(r"(?:Train_|T-)?(\d+)", str(train_id), re.IGNORECASE)
    return int(match.group(1)) if match else None


def get_unavailable_train_ids(cursor) -> set:
    """Return trains already committed to active/recent schedules.

    A train is unavailable if:
    - it has an active tracking leg (planned/in_transit/dwell_time), or
    - it was assigned in a schedule created today and has not been completed.

    This prevents the next auto-schedule from reusing trains already assigned,
    without changing how schedules themselves are created or stored.
    """
    unavailable = set()

    # Trains currently being tracked or waiting on station dwell.
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'train_trip_legs'
        ) AS table_exists
        """
    )
    row = cursor.fetchone()
    tracking_table_exists = bool(row.get("table_exists")) if row else False
    if tracking_table_exists:
        cursor.execute(
            """
            SELECT DISTINCT train_id
            FROM train_trip_legs
            WHERE leg_status IN ('planned', 'in_transit', 'dwell_time')
            """
        )
        for row in cursor.fetchall():
            train_num = extract_train_number(row.get("train_id"))
            if train_num:
                unavailable.add(train_num)

    # Trains assigned by auto-schedules created today, even before tracking starts.
    try:
        cursor.execute(
            """
            SELECT DISTINCT da.train_id
            FROM daily_assignments da
            JOIN schedules s ON s.schedule_id = da.schedule_id
            WHERE da.action = 'assigned'
              AND s.created_at >= CURRENT_DATE
            """
        )
        for row in cursor.fetchall():
            train_num = extract_train_number(row.get("train_id"))
            if train_num:
                unavailable.add(train_num)
    except Exception:
        pass

    return unavailable

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

def calculate_departure_urgency(departure_date):
    """Calculate urgency score based on requested departure date"""
    if not departure_date:
        return 0  # No departure date specified

    try:
        if isinstance(departure_date, str):
            departure_date = datetime.fromisoformat(departure_date.replace('Z', '+00:00'))
        else:
            departure_date = departure_date

        days_until_departure = (departure_date - datetime.now()).days

        if days_until_departure <= 1:   # Today or tomorrow
            return 20  # High urgency
        elif days_until_departure <= 3:  # Within 3 days
            return 15  # Medium urgency
        elif days_until_departure <= 7:  # Within 1 week
            return 10  # Low urgency
        else:
            return 0   # No urgency

    except Exception:
        return 0

@router.post("/auto-schedule", response_model=AutoScheduleResponse)
async def create_auto_schedule(
    request: AutoScheduleRequest,
    current_user: UserInDB = Depends(require_permission(Permission.RUN_SCHEDULER))
):
    """Create automatic schedule based on priority queue"""
    try:
        conn = get_db_connection()
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
        AND created_at >= CURRENT_DATE - INTERVAL '90 days'
        AND order_id NOT IN (
            SELECT DISTINCT order_id
            FROM customer_orders
            WHERE status = 'scheduled'
            AND updated_at >= CURRENT_DATE - INTERVAL '7 days'
        )
        ORDER BY
            CASE priority_level
                WHEN 1 THEN 1  -- Emergency
                WHEN 2 THEN 2  -- Urgent
                WHEN 3 THEN 3  -- Priority
                WHEN 4 THEN 4  -- Normal
                WHEN 5 THEN 5  -- Low
                ELSE 6
            END ASC,
            created_at DESC
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

        # Phase 1: Priority Threshold Filtering
        MIN_PRIORITY_SCORE = 20  # Configurable threshold (lowered for testing)
        high_priority_orders = [
            order for order in scored_orders
            if order['priority_score'] >= MIN_PRIORITY_SCORE
        ]

        if not high_priority_orders:
            cursor.close()
            conn.close()
            return AutoScheduleResponse(
                success=False,
                message=f"No high-priority orders found (threshold: {MIN_PRIORITY_SCORE})"
            )

        # Sort by priority score (highest first)
        high_priority_orders.sort(key=lambda x: x['priority_score'], reverse=True)
        scored_orders = high_priority_orders  # Use filtered list

        # Define actual train capacities and remove trains already assigned.
        all_train_capacities = get_train_capacities()
        unavailable_train_ids = get_unavailable_train_ids(cursor)
        requested_train_limit = max(1, min(int(request.num_trains or 20), 20))
        train_capacities = {
            train_id: capacity
            for train_id, capacity in all_train_capacities.items()
            if train_id <= requested_train_limit and train_id not in unavailable_train_ids
        }

        if not train_capacities:
            cursor.close()
            conn.close()
            return AutoScheduleResponse(
                success=False,
                message="No trains available for scheduling. Existing assigned/tracked trains are unavailable."
            )

        # Phase 2 Enhanced: Priority + Departure Date Awareness
        # Calculate total available train capacity
        total_train_capacity = sum(train_capacities.values())

        # Select orders by combined priority score (priority + departure urgency)
        selected_orders = []
        remaining_capacity = total_train_capacity
        total_cargo = 0
        priority_summary = {
            'emergency': 0,
            'urgent': 0,
            'priority': 0,
            'normal': 0
        }

        # Calculate combined scores for all orders
        enhanced_orders = []
        for order in scored_orders:
            departure_date = order.get('requested_departure_date')
            departure_urgency = calculate_departure_urgency(departure_date)

            # Combined score: Priority Score (0-100) + Departure Urgency (0-20)
            combined_score = order['priority_score'] + departure_urgency

            enhanced_order = order.copy()
            enhanced_order['combined_score'] = combined_score
            enhanced_order['departure_urgency'] = departure_urgency
            enhanced_orders.append(enhanced_order)

        # Sort by combined score (highest first)
        enhanced_orders.sort(key=lambda x: x['combined_score'], reverse=True)

        # Select orders by combined score within capacity constraints
        for order in enhanced_orders:
            if order['cargo_weight'] <= remaining_capacity:
                selected_orders.append(order)
                remaining_capacity -= order['cargo_weight']
                total_cargo += order['cargo_weight']

                    # Count priority levels based on combined scores
                if order['combined_score'] >= 90:  # High priority + urgent departure
                    priority_summary['emergency'] += 1
                elif order['combined_score'] >= 70:  # High priority or moderate urgency
                    priority_summary['urgent'] += 1
                elif order['combined_score'] >= 50:  # Moderate priority or low urgency
                    priority_summary['priority'] += 1
                else:
                    priority_summary['normal'] += 1

        if not selected_orders:
            cursor.close()
            conn.close()
            return AutoScheduleResponse(
                success=False,
                message="No orders fit within available train capacity"
            )

        # Group selected orders by route for scheduling
        route_groups = {}
        print(f"DEBUG: ===== ROUTE GROUPING DEBUG =====")
        print(f"DEBUG: Selected orders count: {len(selected_orders)}")
        for order in selected_orders:
            route_key = f"{order['origin_station']}_TO_{order['destination_station']}"
            print(f"DEBUG: Order {order['order_id']} route: {order['origin_station']} to {order['destination_station']} -> key: {route_key}")
            if route_key not in route_groups:
                route_groups[route_key] = []
            route_groups[route_key].append(order)
        print(f"DEBUG: Final route_groups: {list(route_groups.keys())}")
        print(f"DEBUG: ===== END ROUTE GROUPING DEBUG =====")

        # Create simple schedule (bypass RL agent for now)
        schedule_id = f"AUTO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create daily assignments based on priority order
        daily_assignments = []
        day = 0

        # Sort trains by capacity (largest first) for optimal efficiency
        sorted_train_ids = sorted(train_capacities.keys(), key=lambda x: train_capacities[x], reverse=True)

        # Phase 3: Limited same-direction multi-train assignment
        train_index = 0

        # Sort routes by earliest departure date to ensure proper temporal ordering
        routes_with_dates = []
        for route_key, route_orders in route_groups.items():
            # Find earliest departure date for this route
            earliest_departure = None
            for order in route_orders:
                if order.get('requested_departure_date'):
                    order_departure = order['requested_departure_date']
                    if not earliest_departure or order_departure < earliest_departure:
                        earliest_departure = order_departure

            routes_with_dates.append({
                'route_key': route_key,
                'route_orders': route_orders,
                'earliest_departure': earliest_departure
            })

        # Sort by earliest departure date (earliest first)
        routes_with_dates.sort(key=lambda x: x['earliest_departure'] or datetime.max)

        for route_data in routes_with_dates:
            route_key = route_data['route_key']
            route_orders = route_data['route_orders']
            if route_orders and day < request.max_days:
                # Calculate route statistics
                route_cargo = sum(order['cargo_weight'] for order in route_orders)
                avg_priority = sum(order['priority_score'] for order in route_orders) / len(route_orders)

                # Use as many available trains as needed for the selected route cargo.
                # A single train must never carry more than its configured capacity.
                multi_train_justified = route_cargo > max(train_capacities.values())
                max_trains_for_route = len(sorted_train_ids) - train_index

                # Assign trains to this route
                remaining_route_cargo = route_cargo
                trains_assigned = 0

                while remaining_route_cargo > 0 and trains_assigned < max_trains_for_route and train_index < len(sorted_train_ids):
                    # Get the best available train for this cargo
                    train_id = sorted_train_ids[train_index]
                    train_capacity = train_capacities[train_id]

                    # Never assign more cargo to a train than its capacity.
                    cargo_to_assign = min(remaining_route_cargo, train_capacity)

                    daily_assignments.append({
                        'day': day + 1,
                        'assignments': [{
                            'train_id': f"Train_{train_id}_{trains_assigned + 1}" if trains_assigned > 0 else f"Train_{train_id}",
                            'route': route_key.replace('_TO_', ' to '),
                            'cargo_tons': cargo_to_assign,
                            'action': 'assigned',
                            'train_capacity': train_capacity,
                            'utilization': (cargo_to_assign / train_capacity * 100) if train_capacity > 0 else 0,
                            'avg_priority': avg_priority,
                            'multi_train_justified': multi_train_justified
                        }]
                    })

                    remaining_route_cargo -= cargo_to_assign
                    trains_assigned += 1
                    train_index += 1

                # Only increment day if we assigned at least one train
                if trains_assigned > 0:
                    day += 1

        # Calculate performance metrics
        total_cargo_delivered = sum(
            float(assignment['cargo_tons'])
            for day_assignment in daily_assignments
            for assignment in day_assignment['assignments']
            if assignment['action'] == 'assigned'
        )

        # Calculate realistic efficiency based on actual trains used
        # Count actual unique trains used in assignments (handle multi-train IDs)
        train_ids_used = []
        for day_assignment in daily_assignments:
            for assignment in day_assignment['assignments']:
                train_id_parts = assignment['train_id'].split('_')
                # Extract base train number (remove multi-train suffix if present)
                base_train_num = int(train_id_parts[1])
                train_ids_used.append(base_train_num)

        actual_trains_used = len(set(train_ids_used))
        actual_days_used = len(set(day_assignment['day'] for day_assignment in daily_assignments))

        # Calculate actual capacity used
        actual_capacity_used = 0
        for day_assignment in daily_assignments:
            for assignment in day_assignment['assignments']:
                train_id_parts = assignment['train_id'].split('_')
                # Extract base train number (remove multi-train suffix if present)
                base_train_num = int(train_id_parts[1])
                actual_capacity_used += train_capacities[base_train_num]

        # Efficiency based on actual utilization of assigned trains
        efficiency_score = min(total_cargo_delivered / actual_capacity_used, 1.0) if actual_capacity_used > 0 else 0

        # Calculate realistic profit based on cargo type and railway rates
        # Realistic railway cargo rates (ZMW per ton):
        # - Coal: 50-80 ZMW/ton
        # - Copper: 100-150 ZMW/ton (higher value cargo)
        # - Containers: 75-120 ZMW/ton
        # Average rate: 85 ZMW/ton for mixed cargo
        avg_cargo_rate = 85  # ZMW per ton (realistic railway rate)

        performance_metrics = {
            'total_cargo_delivered': total_cargo_delivered,
            'total_reward': total_cargo_delivered * avg_cargo_rate,  # Realistic profit calculation
            'efficiency_score': efficiency_score,
            'days_completed': len(daily_assignments),
            'actual_trains_used': actual_trains_used,
            'actual_days_used': actual_days_used,
            'actual_capacity_used': actual_capacity_used,
            'cargo_rate_used': avg_cargo_rate
        }

        # Create schedule data
        schedule_data = {
            'schedule_id': schedule_id,
            'num_trains': actual_trains_used,  # Use actual trains used, not requested
            'max_days': actual_days_used,     # Use actual days needed, not requested
            'cargo_requirements': {route_key.replace('_TO_', '_'): float(sum(float(order['cargo_weight']) for order in route_orders)) for route_key, route_orders in route_groups.items()},
            'daily_actions': [],
            'daily_assignments': daily_assignments,
            'performance_metrics': performance_metrics,
            'cost_breakdown': {
                'fuel_cost': float(total_cargo_delivered * 50),
                'crew_cost': float(actual_trains_used * actual_days_used * 1000),
                'maintenance_cost': float(total_cargo_delivered * 20),
                'net_profit_zmw': float(total_cargo_delivered * avg_cargo_rate)
            },
            'efficiency_analysis': {
                'cargo_per_train_per_day': float(total_cargo_delivered / (actual_trains_used * actual_days_used)) if actual_trains_used > 0 and actual_days_used > 0 else 0,
                'utilization_rate': float(performance_metrics['efficiency_score'] * 100),
                'total_efficiency': 'High' if performance_metrics['efficiency_score'] > 0.5 else 'Medium'
            },
            'priority_metadata': {
                'based_on_priority': True,
                'orders_count': len(scored_orders),
                'avg_priority_score': float(sum(order['priority_score'] for order in scored_orders) / len(scored_orders)),
                'fleet_size': len(all_train_capacities),
                'available_train_ids': sorted(train_capacities.keys()),
                'unavailable_train_ids': sorted(unavailable_train_ids)
            }
        }

        # Save to database
        save_success = save_schedule_to_database(schedule_data, route_groups)

        # Update order statuses to 'scheduled' - only for orders actually included
        if save_success:
            # Get only the orders that were actually used in the schedule
            scheduled_order_ids = []
            for day_assignment in daily_assignments:
                for assignment in day_assignment['assignments']:
                    # Find orders for this route and mark them as scheduled
                    route_name = assignment['route'].replace(' to ', '_TO_')
                    route_orders = route_groups.get(route_name.replace(' to ', '_TO_'), [])

                    # Calculate how many orders can be scheduled for this route
                    cargo_per_order = 100  # Average cargo per order
                    orders_to_schedule = min(len(route_orders), int(assignment['cargo_tons'] / cargo_per_order))

                    # Add the order IDs that were actually scheduled
                    for i in range(orders_to_schedule):
                        if i < len(route_orders):
                            scheduled_order_ids.append(route_orders[i]['order_id'])

            # Remove duplicates and update only scheduled orders
            scheduled_order_ids = list(set(scheduled_order_ids))

            if scheduled_order_ids:
                update_query = """
                UPDATE customer_orders
                SET status = 'scheduled',
                    updated_at = CURRENT_TIMESTAMP
                WHERE order_id = ANY(%s)
                """

                cursor.execute(update_query, (scheduled_order_ids,))
                conn.commit()

        cursor.close()
        conn.close()

        if save_success:
            return AutoScheduleResponse(
                success=True,
                schedule_id=schedule_id,
                orders_scheduled=len(route_groups),  # Actual routes scheduled
                total_cargo_tons=total_cargo_delivered,  # Actual cargo delivered
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

def save_schedule_to_database(schedule_data, route_groups):
    """Save schedule to database"""
    try:
        print(f"DEBUG: Attempting to save schedule: {schedule_data['schedule_id']}")
        print(f"DEBUG: Schedule data keys: {list(schedule_data.keys())}")

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Insert schedule
        insert_query = """
        INSERT INTO schedules (
            schedule_id, created_at, num_trains, max_days,
            total_cargo_delivered, efficiency_score, total_reward,
            schedule_data, metadata
        ) VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            schedule_data['schedule_id'],
            schedule_data['num_trains'],
            schedule_data['max_days'],
            float(schedule_data['performance_metrics']['total_cargo_delivered']),
            float(schedule_data['performance_metrics']['efficiency_score']),
            float(schedule_data['performance_metrics']['total_reward']),
            json.dumps(schedule_data, cls=DecimalEncoder),
            json.dumps(schedule_data['priority_metadata'], cls=DecimalEncoder)
        ))

        # Insert daily assignments
        for day_assignment in schedule_data['daily_assignments']:
            print(f"DEBUG: Processing day {day_assignment['day']} with {len(day_assignment['assignments'])} assignments")

            for assignment in day_assignment['assignments']:
                print(f"DEBUG: Inserting assignment: {assignment}")

                # Get departure date from orders for this route
                route_name = assignment['route'].replace(' to ', '_TO_')
                route_orders = route_groups.get(route_name, [])
                departure_date = None

                print(f"DEBUG: ===== DEPARTURE DATE DEBUG =====")
                print(f"DEBUG: Assignment route: {assignment['route']}")
                print(f"DEBUG: Route name for lookup: {route_name}")
                print(f"DEBUG: Available route_groups keys: {list(route_groups.keys())}")
                print(f"DEBUG: Route {route_name} has {len(route_orders)} orders")
                print(f"DEBUG: Route orders: {route_orders}")

                # Find the earliest requested departure date from orders for this route
                for order in route_orders:
                    print(f"DEBUG: Order {order.get('order_id')} has requested_departure_date: {order.get('requested_departure_date')}")
                    if order.get('requested_departure_date'):
                        order_departure = order['requested_departure_date']
                        print(f"DEBUG: Found departure date: {order_departure}")
                        if not departure_date or order_departure < departure_date:
                            departure_date = order_departure
                            print(f"DEBUG: Updated departure_date to: {departure_date}")

                print(f"DEBUG: Final departure_date for assignment: {departure_date}")
                print(f"DEBUG: ===== END DEPARTURE DATE DEBUG =====")

                insert_query = """
                INSERT INTO daily_assignments (
                    schedule_id, day, train_id, route, cargo_tons, action, departure_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """

                cursor.execute(insert_query, (
                    schedule_data['schedule_id'],
                    day_assignment['day'],
                    assignment['train_id'],
                    assignment['route'],
                    float(assignment['cargo_tons']),
                    assignment['action'],
                    departure_date
                ))

        conn.commit()
        print(f"DEBUG: Database commit successful")
        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"ERROR saving schedule: {e}")
        print(f"ERROR Type: {type(e)}")
        print(f"ERROR Args: {e.args}")
        if conn:
            conn.rollback()
        return False

@router.get("/auto-schedule/list")
async def list_schedules(limit: int = Query(50, ge=1, le=100)):
    """List recent auto schedules. `limit` is applied (fixes duplicate route registration)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        schedules_query = """
        SELECT schedule_id, created_at, num_trains, max_days,
               total_cargo_delivered, efficiency_score, total_reward,
               schedule_data, metadata
        FROM schedules
        ORDER BY created_at DESC
        LIMIT %s
        """

        cursor.execute(schedules_query, (limit,))
        schedules = []
        for row in cursor.fetchall():
            schedule = dict(row)

            # Display-only label for the dashboard schedule list.
            # This does not change scheduling behavior; it only gives the UI a
            # friendly customer name to show instead of the generated AUTO_* id.
            customer_query = """
            SELECT DISTINCT customer_name
            FROM customer_orders
            WHERE (
                assigned_schedule_id = %s
                OR (
                    assigned_schedule_id IS NULL
                    AND status = 'scheduled'
                    AND updated_at BETWEEN %s - INTERVAL '2 minutes' AND %s + INTERVAL '2 minutes'
                )
            )
            ORDER BY customer_name
            LIMIT 3
            """
            cursor.execute(customer_query, (
                schedule["schedule_id"],
                schedule["created_at"],
                schedule["created_at"],
            ))
            customer_names = [customer_row["customer_name"] for customer_row in cursor.fetchall()]
            schedule["display_name"] = ", ".join(customer_names) if customer_names else schedule["schedule_id"]

            if schedule.get("total_reward"):
                schedule["net_profit_zmw"] = float(schedule["total_reward"])
            else:
                schedule["net_profit_zmw"] = 0
            schedules.append(schedule)

        cursor.close()
        conn.close()

        return {
            "success": True,
            "schedules": schedules,
            "total_count": len(schedules),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list schedules: {str(e)}",
        )

@router.get("/auto-schedule/status")
async def get_auto_schedule_status():
    """Get status of auto-scheduling system (must be registered before `/auto-schedule/{schedule_id}`)."""
    print("DEBUG: Auto-schedule status endpoint called")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

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
            "total_orders": stats.get("total_orders", 0),
            "scheduled_orders": stats.get("scheduled_orders", 0),
            "pending_orders": stats.get("pending_orders", 0),
            "completed_orders": stats.get("completed_orders", 0),
            "scheduled_cargo_tons": float(stats.get("scheduled_cargo_tons", 0)),
            "auto_schedule_ready": stats.get("pending_orders", 0) > 0,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get auto-schedule status: {str(e)}",
        )

@router.get("/auto-schedule/{schedule_id}")
async def get_schedule_details(
    schedule_id: str,
    current_user: UserInDB = Depends(require_permission(Permission.VIEW_SCHEDULES))
):
    """Get detailed schedule information including included orders"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get schedule details
        schedule_query = """
        SELECT schedule_id, created_at, num_trains, max_days,
               total_cargo_delivered, efficiency_score, total_reward,
               schedule_data, metadata
        FROM schedules
        WHERE schedule_id = %s
        """

        cursor.execute(schedule_query, (schedule_id,))
        schedule = cursor.fetchone()

        if not schedule:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Schedule not found")

        # Get daily assignments with departure dates
        assignments_query = """
        SELECT day, train_id, route, cargo_tons, action, created_at, departure_date
        FROM daily_assignments
        WHERE schedule_id = %s
        ORDER BY day, train_id
        """

        cursor.execute(assignments_query, (schedule_id,))
        assignments = [dict(row) for row in cursor.fetchall()]

        # Parse schedule data first to get order information
        schedule_data = json.loads(schedule['schedule_data']) if schedule['schedule_data'] else {}
        metadata = json.loads(schedule['metadata']) if schedule['metadata'] else {}

        # Get order count from metadata (stored during schedule creation)
        scheduled_order_count = metadata.get('orders_count', 0)

        # Get sample scheduled orders for display (limit to 50)
        orders_query = """
        SELECT order_id, customer_name, cargo_type, cargo_weight,
               origin_station, destination_station, priority_level,
               requested_departure_date, requested_arrival_date,
               status, created_at, updated_at
        FROM customer_orders
        WHERE status = 'scheduled'
        ORDER BY priority_level ASC, created_at DESC
        LIMIT 50
        """

        cursor.execute(orders_query)
        orders = [dict(row) for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return {
            "success": True,
            "schedule": {
                "schedule_id": schedule['schedule_id'],
                "created_at": schedule['created_at'],
                "num_trains": schedule['num_trains'],
                "max_days": schedule['max_days'],
                "total_cargo_delivered": float(schedule['total_cargo_delivered']),
                "efficiency_score": float(schedule['efficiency_score']),
                "total_reward": float(schedule['total_reward']),
                "performance_metrics": schedule_data.get('performance_metrics', {}),
                "cost_breakdown": {
                    **schedule_data.get('cost_breakdown', {}),
                    'net_profit_zmw': float(schedule['total_reward']) if schedule.get('total_reward') else 0
                },
                "efficiency_analysis": schedule_data.get('efficiency_analysis', {}),
                "priority_metadata": metadata
            },
            "daily_assignments": assignments,
            "scheduled_orders": orders,
            "summary": {
                "total_assignments": len(assignments),
                "total_orders": scheduled_order_count,
                "total_cargo_scheduled": float(sum(order['cargo_weight'] for order in orders)),
                "unique_routes": list(set(assignment['route'] for assignment in assignments)),
                "days_with_assignments": list(set(assignment['day'] for assignment in assignments))
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get schedule details: {str(e)}",
        )
