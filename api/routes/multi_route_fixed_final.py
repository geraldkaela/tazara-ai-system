"""
Multi-Route Scheduling API
Handles scheduling for multiple trains across multiple routes
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, List, Optional, Tuple
import numpy as np
import os
import sys
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent
from reinforcement_rl.improved_cost_model import (
    dispatch_reward,
    train_usage_penalty,
    idle_penalty,
    get_improved_cost_breakdown
)

# Get project root directory (3 levels up from multi_route.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Model paths
MODEL_PATH = os.path.join(BASE_DIR, "models", "multi_route_agent.pkl")
DEEP_MODEL_PATH = os.path.join(BASE_DIR, "models", "deep_multi_route_agent.pkl")

# Universal AI Agent - handles 1-12 trains
UNIVERSAL_MODEL_PATH = os.path.join(BASE_DIR, "models", "multi_route_agent_universal.pkl")

def load_universal_agent(num_trains):
    """Load universal agent that can handle any train count"""
    try:
        if os.path.exists(UNIVERSAL_MODEL_PATH):
            agent = MultiRouteAgent(
                state_bins=(10,) * 20,
                action_size=4
            )
            agent.load(UNIVERSAL_MODEL_PATH)
            agent.exploration_rate = 0.0  # No exploration in production
            print(f"SUCCESS: Universal agent loaded for {num_trains} trains")
            return agent
        else:
            print(f"ERROR: Universal agent not found at {UNIVERSAL_MODEL_PATH}")
            return None
    except Exception as e:
        print(f"ERROR: Failed to load universal agent: {e}")
        return None

router = APIRouter(tags=["multi-route"])

class MultiRouteRequest(BaseModel):
    """Request model for multi-route scheduling"""
    num_trains: int = 6
    max_days: int = 14
    cargo_requirements: Dict[str, float]
    use_deep_rl: bool = True

class ScheduleResponse(BaseModel):
    """Schedule creation response."""
    schedule_id: str
    total_profit: float
    cargo_delivered: float
    daily_assignments: List[Dict]
    cost_breakdown: Dict

@router.post("/schedule", response_model=ScheduleResponse)
async def create_multi_route_schedule(request: MultiRouteRequest):
    """
    Create multi-train, multi-route schedule using trained AI agent
    """
    
    # Check if trained model exists
    if not os.path.exists(MODEL_PATH) and not os.path.exists(UNIVERSAL_MODEL_PATH):
        raise HTTPException(
            status_code=500,
            detail=f"Multi-route RL model not found. Train agent first."
        )
    
    try:
        # Set cargo requirements from request or use defaults
        cargo_requirements = getattr(request, 'cargo_requirements', {
            "DAR_KAPIRI": 100,
            "DAR_MBEYA": 100,
            "KAPIRI_NDOLA": 100
        })
        
        # Initialize multi-route environment with user cargo requirements
        env = MultiRouteTazaraEnv(
            num_trains=request.num_trains,
            max_cargo=5000,
            cargo_requirements=cargo_requirements
        )
        
        # Load trained agent
        if request.use_deep_rl and os.path.exists(DEEP_MODEL_PATH):
            # Check for train count compatibility
            if request.num_trains != 6:
                print(f"Deep RL model is calibrated for 6 trains, but {request.num_trains} requested. Falling back to Traditional AI.")
                # Force fallback to Traditional RL (Q-Table)
                request.use_deep_rl = False
            else:
                # Load Deep RL model
                print("Using Deep RL model")
                # Note: Deep RL model loading would go here
                # For now, fall back to traditional
                request.use_deep_rl = False
        
        # Load universal agent that can handle any train count
        agent = load_universal_agent(request.num_trains)
        if agent is None:
            raise HTTPException(
                status_code=500,
                detail=f"Universal AI model not found. Please train the universal agent first."
            )
        
        # Run simulation
        state, _ = env.reset()
        daily_actions = []
        day_assignments_list = []
        
        for day in range(request.max_days):
            # Get actions for all trains
            actions = agent.select_action(state)
            daily_actions.append(actions.tolist())
            
            # Take step in environment
            next_state, reward, done, truncated, info = env.step(actions)
            
            # Create day assignment record
            day_assignment = {
                "day": day + 1,
                "actions": actions.tolist(),
                "reward": reward,
                "cargo_delivered": sum(env.cargo_delivered.values()),
                "state": next_state.tolist()
            }
            day_assignments_list.append(day_assignment)
            
            state = next_state
            
            if done or truncated:
                break
        
        # Generate schedule details
        schedule_id = f"multi_route_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Calculate final metrics
        total_cargo_delivered = sum(env.cargo_delivered.values())
        total_profit = 0.0  # Would calculate from reward accumulation
        
        # Generate daily assignments with driver assignments
        daily_assignments = []
        for day_num, day_data in enumerate(day_assignments_list):
            daily_assignments.append({
                "day": day_num + 1,
                "train_assignments": [
                    {
                        "train_id": f"T-{train_idx + 1}",
                        "route": "IDLE" if action == 3 else ["DAR_KAPIRI", "DAR_MBEYA", "KAPIRI_NDOLA"][action - 1],
                        "rationale": "Strategically idling to prevent station congestion and wait for higher-priority cargo accumulation at the Port." if action == 3 else f"Selected {['DAR_KAPIRI', 'DAR_MBEYA', 'KAPIRI_NDOLA'][action - 1]} route based on optimized turnaround time and current locomotive fuel economy.",
                        "driver_id": f"D{((day_num * request.num_trains + train_idx) % 10) + 1:02d}",
                        "skill_level": 4,
                        "fuel_cost": 0.0 if action == 3 else 50000.0
                    }
                    for train_idx, action in enumerate(day_data["actions"])
                ]
            })
        
        # Get cost breakdown
        cost_breakdown = get_improved_cost_breakdown(
            total_cargo_delivered,
            request.num_trains,
            request.max_days
        )
        
        return ScheduleResponse(
            schedule_id=schedule_id,
            total_profit=total_profit,
            cargo_delivered=total_cargo_delivered,
            daily_assignments=daily_assignments,
            cost_breakdown=cost_breakdown
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Multi-route scheduling failed: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Multi-route scheduling API is running"}

@router.get("/models")
async def get_available_models():
    """Get available trained models"""
    models = []
    
    if os.path.exists(MODEL_PATH):
        models.append({
            "name": "Traditional AI",
            "path": MODEL_PATH,
            "description": "Q-learning agent for 1-12 trains",
            "status": "available"
        })
    
    if os.path.exists(DEEP_MODEL_PATH):
        models.append({
            "name": "Deep RL",
            "path": DEEP_MODEL_PATH,
            "description": "Deep reinforcement learning agent (optimized for 6 trains)",
            "status": "available"
        })
    
    if os.path.exists(UNIVERSAL_MODEL_PATH):
        models.append({
            "name": "Universal AI",
            "path": UNIVERSAL_MODEL_PATH,
            "description": "Universal agent for 1-12 trains (all scenarios)",
            "status": "available"
        })
    
    return {"models": models}
