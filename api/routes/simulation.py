import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from reinforcement_rl.improved_cost_model import get_improved_cost_breakdown
from database.db_manager import db_manager
import numpy as np

def to_python_types(val):
    """Recursively convert NumPy types to Python types."""
    if isinstance(val, dict):
        return {k: to_python_types(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [to_python_types(x) for x in val]
    elif isinstance(val, np.generic):
        return val.item()
    return val

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/simulation", tags=["simulation"])

class ManualModification(BaseModel):
    train_id: int
    day: int
    new_action: int # 0=idle, 1-3=routes
    reason: str

class SimulationRequest(BaseModel):
    original_schedule_id: str
    modifications: List[ManualModification]

class SimulationResponse(BaseModel):
    status: str
    original_schedule_id: str
    updated_performance: Dict
    updated_costs: Dict
    impact_analysis: Dict
    timestamp: str

@router.post("/evaluate-manual-change", response_model=SimulationResponse)
async def evaluate_manual_change(request: SimulationRequest):
    """
    Evaluate the impact of manual changes to an optimized schedule.
    This provides a 'What-If' sandbox for dispatchers.
    """
    try:
        # 1. Fetch original schedule
        original_schedule = db_manager.get_multi_route_schedule(request.original_schedule_id)
        if not original_schedule:
            raise HTTPException(status_code=404, detail=f"Schedule {request.original_schedule_id} not found")
        
        # 2. Deep copy assignments for simulation
        import copy
        sim_assignments = copy.deepcopy(original_schedule['train_assignments'])
        
        # 3. Apply modifications
        for mod in request.modifications:
            found = False
            for assignment in sim_assignments:
                if assignment['train_id'] == mod.train_id and assignment['day'] == mod.day:
                    assignment['action'] = mod.new_action
                    assignment['route_name'] = ["IDLE", "DAR_KAPIRI", "DAR_MBEYA", "KAPIRI_NDOLA"][mod.new_action]
                    assignment['rationale'] = f"Manual Override: {mod.reason}"
                    found = True
                    break
            if not found:
                logger.warning(f"Could not find assignment for Train {mod.train_id} on Day {mod.day}")

        # 4. Recalculate basic metrics (Simplified simulation)
        # In a real system, we'd step the Environment, but here we estimate
        total_cargo = original_schedule['performance_metrics']['total_cargo_delivered']
        idle_days = sum(1 for a in sim_assignments if a['action'] == 0)
        active_trains = len(set(a['train_id'] for a in sim_assignments if a['action'] > 0))
        
        # Adjust cargo based on actions (Mock logic for simulation)
        # Note: This is an estimation for the 'What-If' view
        cargo_impact = 0
        for mod in request.modifications:
            if mod.new_action == 0: # Switched to idle
                cargo_impact -= 800 # Approximate loss per trip
            else: # Switched to route
                cargo_impact += 800
        
        updated_cargo = max(0, total_cargo + cargo_impact)
        
        # 5. Recalculate Costs using the core model
        updated_costs = get_improved_cost_breakdown(
            cargo_delivered=updated_cargo,
            trains_used=active_trains,
            delay_days=original_schedule['performance_metrics']['delay_days'],
            idle_days=idle_days,
            active_trains=active_trains
        )
        
        # 6. Impact Analysis
        original_profit = original_schedule['cost_breakdown_zmw']['net_profit_zmw']
        profit_diff = updated_costs['net_profit_zmw'] - original_profit
        
        impact_analysis = {
            "profit_delta_zmw": profit_diff,
            "cargo_delta_tons": updated_cargo - total_cargo,
            "efficiency_impact": "positive" if profit_diff > 0 else "negative",
            "recommendation": "Manual change improves profit" if profit_diff > 0 else "Manual change reduces efficiency vs AI baseline"
        }

        return SimulationResponse(
            status="calculated",
            original_schedule_id=request.original_schedule_id,
            updated_performance=to_python_types({
                "total_cargo_delivered": total_cargo,
                "idle_days": idle_days,
                "active_trains": active_trains
            }),
            updated_costs=to_python_types(updated_costs),
            impact_analysis=to_python_types(impact_analysis),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Simulation evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
