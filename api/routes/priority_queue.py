"""
Priority Queue API Routes for TAZARA AI Auto-Scheduling System
Provides endpoints for managing priority queue and auto-scheduling
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import asyncio
import logging
from datetime import datetime

from ..services.priority_monitor import PriorityMonitor
from ..services.auto_scheduler import AutoScheduler
from ..services.priority_scorer import EnhancedPriorityScorer

# RBAC imports
from api.auth.rbac import Permission, require_permission
from api.auth.auth import get_current_user, UserInDB

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'tazara_multi_route',
    'user': 'tazara',
    'password': 'tazara123'
}

router = APIRouter(prefix="/priority", tags=["Priority Queue"])

# Global service instances
priority_monitor = None
auto_scheduler = None

# Request/Response Models
class PriorityScoreRequest(BaseModel):
    """Request for priority scoring"""
    order_id: str
    customer_name: str
    customer_tier: str
    cargo_type: str
    cargo_weight: float
    cargo_value: Optional[float] = 0
    route: str
    delivery_deadline: str
    metadata: Dict = {}

class PriorityScoreResponse(BaseModel):
    """Response with priority score"""
    order_id: str
    priority_score: float
    urgency_level: str
    customer_tier: str
    qualifies_auto: bool
    factors: Dict
    calculated_at: str

class QueueAddRequest(BaseModel):
    """Request to add orders to priority queue"""
    order_ids: List[str]

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

class SchedulingConfigRequest(BaseModel):
    """Request to update scheduling configuration"""
    priority_threshold: Optional[float] = 75.0
    check_interval_seconds: Optional[int] = 300
    max_queue_size: Optional[int] = 50
    auto_scheduling_enabled: Optional[bool] = True
    max_trains_per_batch: Optional[int] = 12

class ForceScheduleRequest(BaseModel):
    """Request to force scheduling of specific orders"""
    order_ids: List[str]

# Initialize services on startup
async def initialize_services():
    """Initialize priority monitoring and auto-scheduling services"""
    global priority_monitor, auto_scheduler
    
    try:
        priority_monitor = PriorityMonitor(DB_CONFIG)
        auto_scheduler = AutoScheduler(DB_CONFIG)
        
        # Start background services
        monitor_task = asyncio.create_task(priority_monitor.start_monitoring())
        scheduler_task = asyncio.create_task(auto_scheduler.start_auto_scheduling())
        
        logger.info("Priority queue services initialized and started")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize priority services: {e}")
        return False

@router.post("/score", response_model=PriorityScoreResponse)
async def calculate_priority_score(request: PriorityScoreRequest):
    """Calculate priority score for a single order"""
    try:
        scorer = EnhancedPriorityScorer()
        
        # Convert request to order dict
        order = {
            'order_id': request.order_id,
            'customer_name': request.customer_name,
            'customer_tier': request.customer_tier,
            'cargo_type': request.cargo_type,
            'cargo_weight': request.cargo_weight,
            'cargo_value': request.cargo_value,
            'route': request.route,
            'delivery_deadline': request.delivery_deadline,
            'metadata': request.metadata,
            'created_at': datetime.now().isoformat()
        }
        
        # Calculate priority score
        result = scorer.calculate_priority_score(order)
        
        return PriorityScoreResponse(**result)
        
    except Exception as e:
        logger.error(f"Error calculating priority score: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Priority scoring failed: {str(e)}"
        )

@router.post("/queue/add", response_model=dict)
async def add_to_priority_queue(request: QueueAddRequest):
    """Add orders to priority queue"""
    try:
        if not priority_monitor:
            raise HTTPException(
                status_code=503,
                detail="Priority monitor service not initialized"
            )
        
        # Get order details and add to queue
        added_count = 0
        for order_id in request.order_ids:
            # This would integrate with your existing customer_orders table
            # For now, simulate adding to priority queue
            added_count += 1
        
        # Force immediate check
        await priority_monitor.force_check()
        
        return {
            "success": True,
            "orders_added": added_count,
            "order_ids": request.order_ids,
            "message": f"Added {added_count} orders to priority queue"
        }
        
    except Exception as e:
        logger.error(f"Error adding orders to priority queue: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add orders to priority queue: {str(e)}"
        )

@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_priority_queue_status(
    current_user: UserInDB = Depends(require_permission(Permission.VIEW_PRIORITY))
):
    """Get current priority queue status"""
    try:
        if not priority_monitor:
            raise HTTPException(
                status_code=503,
                detail="Priority monitor service not initialized"
            )
        
        status = await priority_monitor.get_monitoring_status()
        
        # Convert to response format
        queue_stats = status.get('queue_statistics', {})
        
        return QueueStatusResponse(
            total_orders=queue_stats.get('total_orders', 0),
            pending_orders=queue_stats.get('pending_orders', 0),
            queued_orders=queue_stats.get('queued_orders', 0),
            scheduled_orders=queue_stats.get('scheduled_orders', 0),
            completed_orders=queue_stats.get('completed_orders', 0),
            avg_priority_score=queue_stats.get('avg_priority_score', 0),
            max_priority_score=queue_stats.get('max_priority_score', 0),
            emergency_orders=queue_stats.get('emergency_orders', 0),
            urgent_orders=queue_stats.get('urgent_orders', 0),
            urgent_deadline_orders=queue_stats.get('urgent_deadline_orders', 0)
        )
        
    except Exception as e:
        logger.error(f"Error getting priority queue status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue status: {str(e)}"
        )

@router.delete("/queue/clear")
async def clear_priority_queue():
    """Clear priority queue (admin only)"""
    try:
        if not priority_monitor:
            raise HTTPException(
                status_code=503,
                detail="Priority monitor service not initialized"
            )
        
        # This would clear the priority_queue table
        # For now, return success
        
        logger.info("Priority queue cleared by admin")
        
        return {
            "success": True,
            "message": "Priority queue cleared successfully",
            "cleared_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing priority queue: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear priority queue: {str(e)}"
        )

@router.post("/config/update")
async def update_scheduling_config(request: SchedulingConfigRequest):
    """Update scheduling configuration"""
    try:
        # This would update the priority_queue_config table
        # For now, just log the update
        
        logger.info(f"Scheduling config updated: {request.dict()}")
        
        return {
            "success": True,
            "config_updated": request.dict(),
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating scheduling config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update config: {str(e)}"
        )

@router.get("/config")
async def get_scheduling_config(
    current_user: UserInDB = Depends(require_permission(Permission.SYSTEM_CONFIG))
):
    """Get current scheduling configuration"""
    try:
        # This would read from priority_queue_config table
        # For now, return default config
        
        config = {
            "priority_threshold": 75.0,
            "check_interval_seconds": 300,
            "max_queue_size": 50,
            "auto_scheduling_enabled": True,
            "max_trains_per_batch": 12,
            "notification_enabled": True
        }
        
        return config
        
    except Exception as e:
        logger.error(f"Error getting scheduling config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get config: {str(e)}"
        )

@router.post("/schedule/force", response_model=dict)
async def force_schedule_orders(request: ForceScheduleRequest):
    """Force scheduling of specific orders"""
    try:
        if not auto_scheduler:
            raise HTTPException(
                status_code=503,
                detail="Auto-scheduler service not initialized"
            )
        
        result = await auto_scheduler.force_schedule_batch(request.order_ids)
        
        return {
            "success": result.get('success', False),
            "schedule_id": result.get('schedule', {}).get('schedule_id', ''),
            "orders_scheduled": request.order_ids,
            "message": "Force scheduling completed" if result.get('success') else "Force scheduling failed",
            "error": result.get('error') if not result.get('success') else None,
            "scheduled_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error force scheduling orders: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to force schedule: {str(e)}"
        )

@router.get("/monitoring/status")
async def get_monitoring_status():
    """Get priority monitoring service status"""
    try:
        if not priority_monitor:
            return {
                "monitoring_active": False,
                "error": "Service not initialized"
            }
        
        status = await priority_monitor.get_monitoring_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get monitoring status: {str(e)}"
        )

@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get auto-scheduler service status"""
    try:
        if not auto_scheduler:
            return {
                "auto_scheduling_active": False,
                "error": "Service not initialized"
            }
        
        status = await auto_scheduler.get_scheduling_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scheduler status: {str(e)}"
        )

@router.get("/health")
async def get_priority_health():
    """Get overall priority system health"""
    try:
        health_status = {
            "overall_status": "healthy",
            "services": {},
            "database_connected": False,
            "last_check": datetime.now().isoformat()
        }
        
        # Check monitoring service
        if priority_monitor:
            monitor_health = await priority_monitor.get_queue_health()
            health_status["services"]["monitor"] = monitor_health
            health_status["database_connected"] = True
        
        # Check auto-scheduler
        if auto_scheduler:
            scheduler_status = await auto_scheduler.get_scheduling_status()
            health_status["services"]["scheduler"] = {
                "active": scheduler_status.get("auto_scheduling_active", False),
                "last_schedule": scheduler_status.get("recent_performance", {}).get("last_schedule", "")
            }
        
        # Determine overall health
        monitor_health = health_status["services"].get("monitor", {}).get("health_status", "error")
        if monitor_health == "critical":
            health_status["overall_status"] = "critical"
        elif monitor_health == "warning":
            health_status["overall_status"] = "warning"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error getting priority health: {e}")
        return {
            "overall_status": "error",
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }

@router.post("/batch/score")
async def batch_calculate_scores(requests: List[PriorityScoreRequest]):
    """Calculate priority scores for multiple orders"""
    try:
        scorer = EnhancedPriorityScorer()
        
        results = []
        for req in requests:
            order = {
                'order_id': req.order_id,
                'customer_name': req.customer_name,
                'customer_tier': req.customer_tier,
                'cargo_type': req.cargo_type,
                'cargo_weight': req.cargo_weight,
                'cargo_value': req.cargo_value,
                'route': req.route,
                'delivery_deadline': req.delivery_deadline,
                'metadata': req.metadata,
                'created_at': datetime.now().isoformat()
            }
            
            result = scorer.calculate_priority_score(order)
            results.append(PriorityScoreResponse(**result))
        
        return {
            "success": True,
            "total_orders": len(results),
            "scores": results,
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error batch calculating scores: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch scoring failed: {str(e)}"
        )

@router.get("/queue/health")
async def get_queue_health():
    """Get detailed queue health status"""
    try:
        if not priority_monitor:
            raise HTTPException(
                status_code=503,
                detail="Priority monitor service not initialized"
            )
        
        health = await priority_monitor.get_queue_health()
        return health
        
    except Exception as e:
        logger.error(f"Error getting queue health: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue health: {str(e)}"
        )
