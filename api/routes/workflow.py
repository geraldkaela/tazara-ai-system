"""
Workflow Management API Routes
Handles schedule approval, customer orders, modifications, and cancellations
"""

import os
import sys
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db_manager import db_manager

# RBAC imports
from api.auth.rbac import Permission, require_permission
from api.auth.auth import get_current_user, UserInDB

router = APIRouter()

# ========================================
# Pydantic Models
# ========================================

class CustomerOrder(BaseModel):
    customer_name: str
    cargo_type: str
    cargo_weight: float
    origin_station: str
    destination_station: str
    priority_level: int = 3
    requested_departure_date: Optional[date] = None
    requested_arrival_date: Optional[date] = None
    special_requirements: Dict = {}
    notes: Optional[str] = None

class ScheduleApproval(BaseModel):
    approval_status: str  # approved, rejected, needs_revision
    approver_id: str
    approver_name: str
    rejection_reason: Optional[str] = None
    revision_notes: Optional[str] = None
    approval_level: int = 1

class ScheduleModification(BaseModel):
    modification_type: str  # train_add, train_remove, time_adjust, priority_change
    modification_details: Dict
    modified_by: str
    approval_required: bool = True

class TrainCancellation(BaseModel):
    schedule_id: str
    train_id: int
    cancellation_reason: str
    cancelled_by: str
    alternative_arrangements: Optional[Dict] = None

class SchedulingPriority(BaseModel):
    priority_name: str
    weight_speed: float
    weight_fuel: float
    weight_cost: float
    is_active: bool = True

class SchedulingRule(BaseModel):
    rule_name: str
    rule_type: str
    rule_conditions: Dict
    rule_actions: Dict
    priority_level: int = 1
    is_active: bool = True

# ========================================
# CUSTOMER ORDERS
# ========================================

@router.post("/orders", response_model=Dict)
async def create_customer_order(
    order: CustomerOrder,
    current_user: UserInDB = Depends(require_permission(Permission.CREATE_ORDER))
):
    """Create a new customer order"""
    try:
        # Generate order ID
        order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        query = """
            INSERT INTO customer_orders 
            (order_id, customer_name, cargo_type, cargo_weight, origin_station, 
             destination_station, priority_level, requested_departure_date, 
             requested_arrival_date, special_requirements, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
            RETURNING id, order_id, created_at
        """
        
        params = (
            order_id, order.customer_name, order.cargo_type, order.cargo_weight,
            order.origin_station, order.destination_station, order.priority_level,
            order.requested_departure_date, order.requested_arrival_date,
            json.dumps(order.special_requirements), order.notes
        )
        
        result = db_manager.execute_query(query, params)
        
        return {
            "status": "success",
            "order_id": order_id,
            "message": "Customer order created successfully",
            "order": result[0] if result else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create customer order: {str(e)}")

@router.get("/orders", response_model=List[Dict])
async def get_customer_orders(
    status: Optional[str] = None,
    priority: Optional[int] = None,
    limit: int = Query(50, le=100),
    offset: int = 0
):
    """Get customer orders with optional filtering"""
    try:
        query = "SELECT * FROM customer_orders WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if priority:
            query += " AND priority_level = %s"
            params.append(priority)
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        print(f"DEBUG: Workflow orders query: {query}")
        print(f"DEBUG: Workflow orders params: {params}")
        
        result = db_manager.execute_query(query, tuple(params))
        print(f"DEBUG: Workflow orders returned: {len(result)} orders")
        if result:
            print(f"DEBUG: First workflow order: {result[0]}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve customer orders: {str(e)}")

@router.get("/orders/{order_id}", response_model=Dict)
async def get_customer_order(order_id: str):
    """Get specific customer order details"""
    try:
        query = "SELECT * FROM customer_orders WHERE order_id = %s"
        result = db_manager.execute_query(query, (order_id,))
        
        if not result:
            raise HTTPException(status_code=404, detail="Customer order not found")
        
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve customer order: {str(e)}")

@router.put("/orders/{order_id}/assign")
async def assign_order_to_schedule(order_id: str, schedule_id: str, train_id: int):
    """Assign a customer order to a specific schedule and train"""
    try:
        query = """
            UPDATE customer_orders 
            SET assigned_schedule_id = %s, assigned_train_id = %s, 
                status = 'assigned', updated_at = NOW()
            WHERE order_id = %s
            RETURNING *
        """
        
        result = db_manager.execute_query(query, (schedule_id, train_id, order_id))
        
        if not result:
            raise HTTPException(status_code=404, detail="Customer order not found")
        
        return {
            "status": "success",
            "message": "Order assigned successfully",
            "order": result[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign order: {str(e)}")

# ========================================
# SCHEDULE APPROVAL WORKFLOW
# ========================================

@router.post("/schedules/{schedule_id}/approve", response_model=Dict)
async def approve_schedule(schedule_id: str, approval: ScheduleApproval):
    """Approve or reject a schedule"""
    try:
        # Check if schedule exists
        schedule_query = "SELECT schedule_id FROM multi_route_schedules WHERE schedule_id = %s"
        schedule_result = db_manager.execute_query(schedule_query, (schedule_id,))
        
        if not schedule_result:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Check if approval already exists
        existing_query = "SELECT id FROM schedule_approvals WHERE schedule_id = %s"
        existing_result = db_manager.execute_query(existing_query, (schedule_id,))
        
        if existing_result:
            # Update existing approval (without updated_at to avoid trigger issues)
            query = """
                UPDATE schedule_approvals 
                SET approval_status = %s, approver_id = %s, approver_name = %s,
                    rejection_reason = %s, revision_notes = %s, approval_level = %s,
                    approval_date = NOW()
                WHERE schedule_id = %s
            """
            params = (
                approval.approval_status, approval.approver_id, approval.approver_name,
                approval.rejection_reason, approval.revision_notes, approval.approval_level,
                schedule_id
            )
            try:
                db_manager.execute_query(query, params)
            except Exception as e:
                if "no results to fetch" in str(e):
                    # Expected for UPDATE operations, ignore and continue
                    pass
                else:
                    raise e
            
            # Get the updated record
            result_query = "SELECT * FROM schedule_approvals WHERE schedule_id = %s"
            result = db_manager.execute_query(result_query, (schedule_id,))
            
            return {
                "status": "success",
                "message": f"Schedule {approval.approval_status} successfully",
                "approval": result[0] if result else None
            }
        else:
            # Insert new approval (without updated_at to avoid trigger issues)
            query = """
                INSERT INTO schedule_approvals 
                (schedule_id, approval_status, approver_id, approver_name, 
                 rejection_reason, revision_notes, approval_level, approval_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            params = (
                schedule_id, approval.approval_status, approval.approver_id,
                approval.approver_name, approval.rejection_reason,
                approval.revision_notes, approval.approval_level
            )
            try:
                db_manager.execute_query(query, params)
            except Exception as e:
                if "no results to fetch" in str(e):
                    # Expected for INSERT operations, ignore and continue
                    pass
                else:
                    raise e
            
            # Get the inserted record
            result_query = "SELECT * FROM schedule_approvals WHERE schedule_id = %s"
            result = db_manager.execute_query(result_query, (schedule_id,))
            
            return {
                "status": "success",
                "message": f"Schedule {approval.approval_status} successfully",
                "approval": result[0] if result else None
            }
        
        # Update schedule status if approved
        if approval.approval_status == "approved":
            update_query = """
                UPDATE multi_route_schedules 
                SET status = 'approved'
                WHERE schedule_id = %s
            """
            db_manager.execute_query(update_query, (schedule_id,))
        elif approval.approval_status == "rejected":
            update_query = """
                UPDATE multi_route_schedules 
                SET status = 'rejected'
                WHERE schedule_id = %s
            """
            db_manager.execute_query(update_query, (schedule_id,))
        
        return {
            "status": "success",
            "message": f"Schedule {approval.approval_status} successfully",
            "approval": result[0] if result else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process approval: {str(e)}")

@router.get("/schedules/{schedule_id}/approval", response_model=Dict)
async def get_schedule_approval_status(schedule_id: str):
    """Get approval status for a schedule"""
    try:
        query = "SELECT * FROM schedule_approvals WHERE schedule_id = %s"
        result = db_manager.execute_query(query, (schedule_id,))
        
        if not result:
            return {
                "schedule_id": schedule_id,
                "approval_status": "pending",
                "message": "No approval record found"
            }
        
        return result[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get approval status: {str(e)}")

# ========================================
# SCHEDULE MODIFICATIONS
# ========================================

@router.post("/schedules/{schedule_id}/modify", response_model=Dict)
async def modify_schedule(schedule_id: str, modification: ScheduleModification):
    """Submit a schedule modification request"""
    try:
        # Get current schedule data for comparison
        current_query = "SELECT * FROM multi_route_schedules WHERE schedule_id = %s"
        current_result = db_manager.execute_query(current_query, (schedule_id,))
        
        if not current_result:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        current_schedule = current_result[0]
        
        # Insert modification record
        query = """
            INSERT INTO schedule_modifications 
            (schedule_id, modification_type, modification_details, 
             previous_values, modified_by, approval_required, modification_date)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        
        # Convert current_schedule to JSON-safe format
        current_schedule_json = {}
        for key, value in current_schedule.items():
            if isinstance(value, datetime):
                current_schedule_json[key] = value.isoformat()
            elif isinstance(value, date):
                current_schedule_json[key] = value.isoformat()
            else:
                current_schedule_json[key] = value
        
        params = (
            schedule_id, modification.modification_type,
            json.dumps(modification.modification_details), json.dumps(current_schedule_json),
            modification.modified_by, modification.approval_required
        )
        
        try:
            db_manager.execute_query(query, params)
        except Exception as e:
            if "no results to fetch" in str(e):
                # Expected for INSERT operations, ignore and continue
                pass
            else:
                raise HTTPException(status_code=500, detail=f"Failed to insert modification: {str(e)}")
        
        # Get the inserted record using a simpler approach
        try:
            result = db_manager.execute_query("SELECT * FROM schedule_modifications WHERE schedule_id = %s ORDER BY id DESC LIMIT 1", (schedule_id,))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve modification: {str(e)}")
        
        return {
            "status": "success",
            "message": "Schedule modification submitted successfully",
            "modification_id": result[0]["id"] if result else None,
            "requires_approval": modification.approval_required
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Modification endpoint error: {str(e)}")  # Debug log
        print(f"DEBUG: Error type: {type(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=f"Failed to process modification: {str(e)}")

@router.get("/schedules/{schedule_id}/modifications", response_model=List[Dict])
async def get_schedule_modifications(schedule_id: str):
    """Get modification history for a schedule"""
    try:
        query = """
            SELECT * FROM schedule_modifications 
            WHERE schedule_id = %s 
            ORDER BY modification_date DESC
        """
        return db_manager.execute_query(query, (schedule_id,))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get modifications: {str(e)}")

# ========================================
# TRAIN CANCELLATIONS
# ========================================

@router.post("/schedules/{schedule_id}/cancel-train", response_model=Dict)
async def cancel_train(schedule_id: str, cancellation: TrainCancellation):
    """Cancel a train from a schedule"""
    try:
        # Check if schedule exists
        schedule_query = "SELECT schedule_id FROM multi_route_schedules WHERE schedule_id = %s"
        schedule_result = db_manager.execute_query(schedule_query, (schedule_id,))
        
        if not schedule_result:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Insert cancellation record
        query = """
            INSERT INTO train_cancellations 
            (schedule_id, train_id, cancellation_reason, cancelled_by, 
             alternative_arrangements)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, cancellation_date
        """
        
        params = (
            schedule_id, cancellation.train_id, cancellation.cancellation_reason,
            cancellation.cancelled_by, cancellation.alternative_arrangements
        )
        
        result = db_manager.execute_query(query, params)
        
        return {
            "status": "success",
            "message": "Train cancelled successfully",
            "cancellation_id": result[0]["id"] if result else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel train: {str(e)}")

@router.get("/schedules/{schedule_id}/cancellations", response_model=List[Dict])
async def get_train_cancellations(schedule_id: str):
    """Get cancellation history for a schedule"""
    try:
        query = """
            SELECT * FROM train_cancellations 
            WHERE schedule_id = %s 
            ORDER BY cancellation_date DESC
        """
        return db_manager.execute_query(query, (schedule_id,))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cancellations: {str(e)}")

# ========================================
# SCHEDULING PRIORITIES
# ========================================

@router.get("/priorities", response_model=List[Dict])
async def get_scheduling_priorities():
    """Get all scheduling priority configurations"""
    try:
        query = "SELECT * FROM scheduling_priorities WHERE is_active = TRUE ORDER BY priority_name"
        return db_manager.execute_query(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get priorities: {str(e)}")

@router.post("/priorities", response_model=Dict)
async def create_scheduling_priority(priority: SchedulingPriority):
    """Create a new scheduling priority configuration"""
    try:
        query = """
            INSERT INTO scheduling_priorities 
            (priority_name, weight_speed, weight_fuel, weight_cost, is_active)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """
        
        params = (
            priority.priority_name, priority.weight_speed,
            priority.weight_fuel, priority.weight_cost, priority.is_active
        )
        
        result = db_manager.execute_query(query, params)
        
        return {
            "status": "success",
            "message": "Scheduling priority created successfully",
            "priority": result[0] if result else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create priority: {str(e)}")

# ========================================
# SCHEDULING RULES
# ========================================

@router.get("/rules", response_model=List[Dict])
async def get_scheduling_rules():
    """Get all scheduling rules"""
    try:
        query = "SELECT * FROM scheduling_rules WHERE is_active = TRUE ORDER BY priority_level, rule_name"
        return db_manager.execute_query(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rules: {str(e)}")

@router.post("/rules", response_model=Dict)
async def create_scheduling_rule(rule: SchedulingRule):
    """Create a new scheduling rule"""
    try:
        query = """
            INSERT INTO scheduling_rules 
            (rule_name, rule_type, rule_conditions, rule_actions, 
             priority_level, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        
        params = (
            rule.rule_name, rule.rule_type, rule.rule_conditions,
            rule.rule_actions, rule.priority_level, rule.is_active
        )
        
        result = db_manager.execute_query(query, params)
        
        return {
            "status": "success",
            "message": "Scheduling rule created successfully",
            "rule": result[0] if result else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create rule: {str(e)}")

@router.post("/rules/validate", response_model=Dict)
async def validate_schedule_against_rules(schedule_data: Dict):
    """Validate a schedule against all active rules"""
    try:
        # Get all active rules
        rules_query = "SELECT * FROM scheduling_rules WHERE is_active = TRUE ORDER BY priority_level"
        rules = db_manager.execute_query(rules_query)
        
        violations = []
        warnings = []
        
        for rule in rules:
            # Simple rule validation logic (can be enhanced)
            conditions = rule["rule_conditions"]
            actions = rule["rule_actions"]
            
            # Example validation for max operating hours
            if rule["rule_type"] == "time_window" and "max_hours" in conditions:
                # Check if schedule exceeds max hours (simplified)
                if "daily_actions" in schedule_data:
                    # Add actual validation logic here
                    pass
            
            # Example validation for minimum cargo
            if rule["rule_type"] == "capacity" and "min_cargo_tons" in conditions:
                if "cargo_requirements" in schedule_data:
                    # Add actual validation logic here
                    pass
        
        return {
            "status": "success",
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "rules_checked": len(rules)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate rules: {str(e)}")
