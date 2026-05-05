"""
Simple Priority Queue API Routes
Basic endpoints for priority queue management
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

router = APIRouter(tags=["Priority Queue"])

# Priority scoring function
def calculate_priority_score(order):
    """Calculate priority score for an order"""
    score = 0
    urgency_level = "normal"
    breakdown = {}
    
    # Base score from priority_level (1=highest, 5=lowest)
    priority_level = order.get('priority_level', 3)
    if priority_level == 1:
        score += 40
        urgency_level = "emergency"
        breakdown['Priority Level 1 (Emergency)'] = 40
    elif priority_level == 2:
        score += 30
        urgency_level = "urgent"
        breakdown['Priority Level 2 (Urgent)'] = 30
    elif priority_level == 3:
        score += 20
        urgency_level = "priority"
        breakdown['Priority Level 3 (Priority)'] = 20
    elif priority_level == 4:
        score += 10
        breakdown['Priority Level 4 (Normal)'] = 10
    else:
        score += 5
        breakdown['Priority Level 5 (Low)'] = 5
    
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
                breakdown[f'Deadline: {days_until_deadline} days (Emergency)'] = 30
            elif days_until_deadline <= 3:
                score += 20
                urgency_level = "urgent"
                breakdown[f'Deadline: {days_until_deadline} days (Urgent)'] = 20
            elif days_until_deadline <= 7:
                score += 10
                urgency_level = "priority"
                breakdown[f'Deadline: {days_until_deadline} days (Priority)'] = 10
            else:
                breakdown[f'Deadline: {days_until_deadline} days (Normal)'] = 0
        except:
            breakdown['Deadline: Error parsing'] = 0
    else:
        breakdown['Deadline: Not set'] = 0
    
    # Cargo weight bonus (larger shipments get priority)
    cargo_weight = order.get('cargo_weight', 0)
    if cargo_weight > 1000:
        score += 10
        breakdown[f'Cargo Weight: {cargo_weight} tons (>1000)'] = 10
    elif cargo_weight > 500:
        score += 5
        breakdown[f'Cargo Weight: {cargo_weight} tons (>500)'] = 5
    elif cargo_weight > 200:
        score += 3
        breakdown[f'Cargo Weight: {cargo_weight} tons (>200)'] = 3
    else:
        breakdown[f'Cargo Weight: {cargo_weight} tons (Small)'] = 0
    
    # Special cargo types
    cargo_type = order.get('cargo_type', '').lower()
    if any(keyword in cargo_type for keyword in ['medical', 'emergency', 'urgent', 'perishable']):
        score += 15
        urgency_level = "emergency"
        breakdown[f'Cargo Type: {cargo_type} (Emergency)'] = 15
    elif any(keyword in cargo_type for keyword in ['copper', 'minerals', 'coal', 'fuel']):
        score += 10
        breakdown[f'Cargo Type: {cargo_type} (Minerals/Fuel)'] = 10
    elif any(keyword in cargo_type for keyword in ['manufactured', 'machinery']):
        score += 5
        breakdown[f'Cargo Type: {cargo_type} (Manufactured)'] = 5
    else:
        breakdown[f'Cargo Type: {cargo_type} (Standard)'] = 0
    
    # Route distance bonus (longer routes get priority)
    origin = order.get('origin_station', '').lower()
    dest = order.get('destination_station', '').lower()
    
    # Check for full TAZARA route (both directions)
    if ('dar es salaam' in origin and 'kapiri' in dest) or ('kapiri' in origin and 'dar es salaam' in dest):
        score += 10
        breakdown['Route: Full TAZARA route'] = 10
    elif 'dar es salaam' in origin or 'kapiri' in dest or 'mbeya' in origin or 'mbeya' in dest:
        score += 5
        breakdown['Route: Partial TAZARA route'] = 5
    else:
        breakdown[f'Route: {origin} to {dest}'] = 0
    
    # Customer name recognition (repeat customers get bonus)
    customer_name = order.get('customer_name', '').lower()
    if any(keyword in customer_name for keyword in ['government', 'ministry', 'corporation', 'ltd']):
        score += 5
        breakdown[f'Customer: {customer_name} (Corporate)'] = 5
    else:
        breakdown[f'Customer: {customer_name} (Standard)'] = 0
    
    # Cap at 100
    final_score = min(score, 100)
    if final_score < score:
        breakdown['Score capped at 100'] = score - final_score
    
    return {
        'priority_score': final_score,
        'urgency_level': urgency_level,
        'breakdown': breakdown
    }

# Response Models
class QueueStatusResponse(BaseModel):
    """Response with queue status"""
    total_orders: int
    pending_orders: int
    queued_orders: int
    scheduled_orders: int
    completed_orders: int
    avg_priority_score: float
    max_priority_score: float
    emergency_orders: int
    urgent_orders: int
    urgent_deadline_orders: int

class HealthResponse(BaseModel):
    """Health check response"""
    overall_status: str
    database_connected: bool
    last_check: str
    queue_size: Optional[int] = None

@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_priority_queue_status():
    """Get current priority queue status from customer orders"""
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
        
        cursor.execute(orders_query)
        orders = [dict(row) for row in cursor.fetchall()]
        print(f"DEBUG: SQL query returned {len(orders)} orders")
        print(f"DEBUG: SQL query: {orders_query}")
        if orders:
            print(f"DEBUG: First order sample: {orders[0]}")
        
        # Calculate priority scores for each order
        scored_orders = []
        for order in orders:
            score = calculate_priority_score(order)
            order['priority_score'] = score['priority_score']
            order['urgency_level'] = score['urgency_level']
            scored_orders.append(order)
        
        # Calculate statistics
        total_orders = len(scored_orders)
        pending_orders = len([o for o in scored_orders if o['status'] == 'pending'])
        queued_orders = len([o for o in scored_orders if o.get('in_priority_queue', False)])
        scheduled_orders = len([o for o in scored_orders if o['status'] == 'scheduled'])
        completed_orders = len([o for o in scored_orders if o['status'] == 'completed'])
        
        avg_priority_score = sum(o['priority_score'] for o in scored_orders) / total_orders if total_orders > 0 else 0
        max_priority_score = max(o['priority_score'] for o in scored_orders) if scored_orders else 0
        emergency_orders = len([o for o in scored_orders if o['urgency_level'] == 'emergency'])
        urgent_orders = len([o for o in scored_orders if o['urgency_level'] == 'urgent'])
        
        # Check urgent deadlines
        urgent_deadline_orders = len([
            o for o in scored_orders 
            if o.get('delivery_deadline') and o['delivery_deadline'] < (datetime.now() + timedelta(days=1)).isoformat()
        ])
        
        cursor.close()
        conn.close()
        
        # Convert to response format
        return QueueStatusResponse(
            total_orders=total_orders,
            pending_orders=pending_orders,
            queued_orders=queued_orders,
            scheduled_orders=scheduled_orders,
            completed_orders=completed_orders,
            avg_priority_score=avg_priority_score,
            max_priority_score=max_priority_score,
            emergency_orders=emergency_orders,
            urgent_orders=urgent_orders,
            urgent_deadline_orders=urgent_deadline_orders
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue status: {str(e)}"
        )

@router.get("/health", response_model=HealthResponse)
async def get_priority_health():
    """Get overall priority system health"""
    try:
        health_status = {
            "overall_status": "healthy",
            "database_connected": False,
            "last_check": datetime.now().isoformat()
        }
        
        # Test database connection
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            health_status["database_connected"] = True
            
            # Get queue size
            cursor = conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM priority_queue WHERE status IN ('pending', 'queued')")
            queue_size = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            health_status["queue_size"] = queue_size
            
            # Determine overall health
            if queue_size > 50:
                health_status["overall_status"] = "warning"
            elif queue_size > 100:
                health_status["overall_status"] = "critical"
                
        except Exception as e:
            health_status["overall_status"] = "error"
            health_status["database_connected"] = False
        
        return HealthResponse(**health_status)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get health status: {str(e)}"
        )

@router.get("/queue/list")
async def get_priority_queue_list():
    """Get list of orders from customer orders with priority scores"""
    print("DEBUG: Priority queue list endpoint called")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get customer orders and calculate priority scores
        query = """
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
        ORDER BY created_at DESC
        """
        
        cursor.execute(query)
        orders = [dict(row) for row in cursor.fetchall()]
        print(f"DEBUG: Queue list SQL query returned {len(orders)} orders")
        print(f"DEBUG: Queue list SQL query: {query}")
        if orders:
            print(f"DEBUG: Queue list first order sample: {orders[0]}")
        
        # Calculate priority scores for each order
        scored_orders = []
        for order in orders:
            score = calculate_priority_score(order)
            order['priority_score'] = score['priority_score']
            order['urgency_level'] = score['urgency_level']
            scored_orders.append(order)
        
        # Sort by priority score (highest first)
        scored_orders.sort(key=lambda x: x['priority_score'], reverse=True)
        
        cursor.close()
        conn.close()
        
        result = {
            "success": True,
            "orders": scored_orders[:20],  # Return top 20
            "total_returned": len(scored_orders[:20])
        }
        print(f"DEBUG: Returning {len(scored_orders[:20])} orders")
        for i, order in enumerate(scored_orders[:3]):  # Show first 3 orders
            print(f"DEBUG: Order {i+1}: {order.get('customer_name', 'Unknown')} - {order.get('cargo_type', 'Unknown')} - {order.get('cargo_weight', 0)} tons")
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue list: {str(e)}"
        )

@router.get("/queue/stats")
async def get_queue_statistics():
    """Get detailed queue statistics"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get statistics by urgency level
        urgency_query = """
        SELECT 
            urgency_level,
            COUNT(*) as count,
            AVG(priority_score) as avg_score,
            MAX(priority_score) as max_score
        FROM priority_queue
        GROUP BY urgency_level
        ORDER BY urgency_level
        """
        
        cursor.execute(urgency_query)
        urgency_stats = [dict(row) for row in cursor.fetchall()]
        
        # Get statistics by customer tier
        tier_query = """
        SELECT 
            customer_tier,
            COUNT(*) as count,
            AVG(priority_score) as avg_score
        FROM priority_queue
        GROUP BY customer_tier
        ORDER BY customer_tier
        """
        
        cursor.execute(tier_query)
        tier_stats = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "urgency_statistics": urgency_stats,
            "tier_statistics": tier_stats,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue statistics: {str(e)}"
        )

@router.post("/queue/clear")
async def clear_priority_queue():
    """Clear priority queue (admin only)"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Clear all orders from priority queue
        cursor.execute("DELETE FROM priority_queue")
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "Priority queue cleared successfully",
            "cleared_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear priority queue: {str(e)}"
        )

@router.get("/")
async def priority_root():
    """Priority API root endpoint"""
    return {
        "message": "TAZARA Priority Auto-Scheduling API",
        "version": "1.0.0",
        "endpoints": {
            "queue_status": "/priority/queue/status",
            "health": "/priority/health",
            "queue_list": "/priority/queue/list",
            "queue_stats": "/priority/queue/stats",
            "clear_queue": "/priority/queue/clear"
        },
        "status": "operational"
    }
