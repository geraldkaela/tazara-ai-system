import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()

CONFIG_FILE = "config/system_config.json"
os.makedirs("config", exist_ok=True)

class ConfigUpdate(BaseModel):
    learning_rate: float = 0.1
    exploration_rate: float = 0.1
    max_trains: int = 6
    planning_horizon: int = 14
    coordination_bonus: bool = True
    # New priority settings
    priority_speed_weight: float = 0.33
    priority_fuel_weight: float = 0.33
    priority_cost_weight: float = 0.34
    optimization_mode: str = "balanced"  # speed, fuel, cost, balanced

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {
        "learning_rate": 0.1,
        "exploration_rate": 0.1,
        "max_trains": 6,
        "planning_horizon": 14,
        "coordination_bonus": True,
        "priority_speed_weight": 0.33,
        "priority_fuel_weight": 0.33,
        "priority_cost_weight": 0.34,
        "optimization_mode": "balanced"
    }

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

@router.get("/")
async def get_config():
    return load_config()

@router.post("/")
async def update_config(config: ConfigUpdate):
    config_dict = config.dict()
    save_config(config_dict)
    return {"status": "success", "config": config_dict}
