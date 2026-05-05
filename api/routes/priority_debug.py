"""
Priority Debug API Routes
Shows detailed priority score calculations for debugging
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

router = APIRouter(tags=["Priority Debug"])

class PriorityBreakdown(BaseModel):
    order_id: str
    customer_name: str
    cargo_type: str
    cargo_weight: float
    priority_level: int
    final_score: int
    urgency_level: str
    scoring_breakdown: Dict[str, int]

def calculate_priority_score_with_breakdown(order):
    """Calculate priority score with detailed breakdown"""
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
    if 'dar es salaam' in origin and 'kapiri' in dest:
        score += 10
        breakdown['Route: Full TAZARA route'] = 10
    elif 'dar es salaam' in origin or 'kapiri' in dest:
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

@router.get("/debug/scoring")
async def get_priority_scoring_debug():
    """Get detailed priority scoring breakdown for all orders"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get customer orders
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
        AND created_at >= CURRENT_DATE - INTERVAL '30 days'
        ORDER BY created_at DESC
        LIMIT 10
        """
        
        cursor.execute(query)
        orders = [dict(row) for row in cursor.fetchall()]
        
        # Calculate priority scores with breakdown
        results = []
        for order in orders:
            scoring = calculate_priority_score_with_breakdown(order)
            
            result = PriorityBreakdown(
                order_id=order['order_id'],
                customer_name=order['customer_name'],
                cargo_type=order['cargo_type'],
                cargo_weight=order['cargo_weight'],
                priority_level=order['priority_level'],
                final_score=scoring['priority_score'],
                urgency_level=scoring['urgency_level'],
                scoring_breakdown=scoring['breakdown']
            )
            results.append(result)
        
        # Sort by final score
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "orders": results,
            "scoring_explanation": {
                "priority_level": "1=40pts (Emergency), 2=30pts (Urgent), 3=20pts (Priority), 4=10pts (Normal), 5=5pts (Low)",
                "deadline": "1 day=30pts, 3 days=20pts, 7 days=10pts",
                "cargo_weight": ">1000 tons=10pts, >500 tons=5pts, >200 tons=3pts",
                "cargo_type": "Medical/Emergency=15pts, Minerals/Fuel=10pts, Manufactured=5pts",
                "route": "Full TAZARA=10pts, Partial=5pts",
                "customer": "Corporate/Government=5pts",
                "max_score": 100
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scoring debug: {str(e)}"
        )
