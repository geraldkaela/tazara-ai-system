"""Labor optimization API routes.

Endpoints for workforce scheduling and cost optimization.
"""
from __future__ import annotations

import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/labor", tags=["labor_optimization"])


class LaborOptimizationRequest(BaseModel):
    """Request for labor optimization."""
    route: str = Field(..., description="Route to optimize for")
    work_date: str = Field(default_factory=lambda: date.today().isoformat(), description="Work date")
    required_skills: List[str] = Field(default=[], description="Required driver skills")
    shift_type: str = Field(default="day", description="Shift type: day, evening, night")
    max_overtime_hours: float = Field(default=4.0, description="Maximum overtime hours allowed")
    min_efficiency_score: float = Field(default=70.0, ge=0, le=100, description="Minimum efficiency score")


class DriverAssignment(BaseModel):
    """Optimized driver assignment."""
    driver_id: str
    driver_name: str
    skill_level: str
    shift_type: str
    regular_hours: float
    overtime_hours: float
    cost_zmw: float
    efficiency_score: float


class LaborCostBreakdown(BaseModel):
    """Labor cost breakdown."""
    regular_cost: float
    overtime_cost: float
    skill_premium: float
    total_cost: float


class LaborOptimizationResponse(BaseModel):
    """Labor optimization results."""
    route: str
    work_date: str
    assignments: List[DriverAssignment]
    cost_breakdown: LaborCostBreakdown
    total_drivers: int
    total_hours: float
    overtime_hours: float
    efficiency_score: float
    cost_savings_zmw: float
    recommendations: List[str]


def optimize_labor_assignments(route: str, required_skills: List[str], shift_type: str) -> List[Dict]:
    """Generate optimized driver assignments."""
    # Mock optimization - in production this would query actual driver database
    
    base_drivers = [
        {
            "driver_id": "DRV001",
            "driver_name": "John Mutale",
            "skill_level": "advanced",
            "efficiency_score": 85.5,
            "base_rate": 70.0
        },
        {
            "driver_id": "DRV002", 
            "driver_name": "Grace Banda",
            "skill_level": "intermediate",
            "efficiency_score": 78.0,
            "base_rate": 65.0
        },
        {
            "driver_id": "DRV003",
            "driver_name": "Peter Zulu",
            "skill_level": "advanced", 
            "efficiency_score": 88.0,
            "base_rate": 70.0
        }
    ]
    
    # Filter by required skills
    if required_skills:
        filtered = [d for d in base_drivers if d["skill_level"] in required_skills]
    else:
        filtered = base_drivers
    
    # Sort by efficiency
    filtered.sort(key=lambda x: x["efficiency_score"], reverse=True)
    
    # Assign hours and calculate costs
    assignments = []
    for i, driver in enumerate(filtered[:3]):  # Max 3 drivers
        regular_hours = 8.0
        overtime_hours = 2.0 if i == 0 else 0.0  # Lead driver gets overtime
        
        # Calculate costs
        regular_cost = regular_hours * driver["base_rate"]
        overtime_cost = overtime_hours * driver["base_rate"] * 1.5  # 1.5x overtime
        
        # Skill premium
        skill_multiplier = 1.4 if driver["skill_level"] == "advanced" else 1.0
        skill_premium = (regular_cost + overtime_cost) * (skill_multiplier - 1)
        
        total_cost = regular_cost + overtime_cost + skill_premium
        
        assignments.append({
            "driver_id": driver["driver_id"],
            "driver_name": driver["driver_name"],
            "skill_level": driver["skill_level"],
            "shift_type": shift_type,
            "regular_hours": regular_hours,
            "overtime_hours": overtime_hours,
            "cost_zmw": round(total_cost, 2),
            "efficiency_score": driver["efficiency_score"]
        })
    
    return assignments


def calculate_cost_breakdown(assignments: List[Dict]) -> Dict:
    """Calculate cost breakdown from assignments."""
    regular_cost = sum(a["regular_hours"] * 70.0 for a in assignments)  # Base rate
    overtime_cost = sum(a["overtime_hours"] * 70.0 * 1.5 for a in assignments)
    skill_premium = sum(a["cost_zmw"] - (a["regular_hours"] * 70.0 + a["overtime_hours"] * 105.0) 
                       for a in assignments)
    
    return {
        "regular_cost": round(regular_cost, 2),
        "overtime_cost": round(overtime_cost, 2),
        "skill_premium": round(max(0, skill_premium), 2),
        "total_cost": round(regular_cost + overtime_cost + max(0, skill_premium), 2)
    }


def generate_recommendations(assignments: List[Dict], route: str) -> List[str]:
    """Generate optimization recommendations."""
    recommendations = []
    
    total_overtime = sum(a["overtime_hours"] for a in assignments)
    avg_efficiency = sum(a["efficiency_score"] for a in assignments) / len(assignments) if assignments else 0
    
    if total_overtime > 4:
        recommendations.append(f"High overtime detected ({total_overtime} hrs). Consider adding relief driver for {route}.")
    
    if avg_efficiency < 80:
        recommendations.append("Driver efficiency below target. Consider refresher training.")
    
    if len(assignments) < 2:
        recommendations.append("Single driver assignment. Recommend backup driver for long routes.")
    
    # Add route-specific recommendations
    if "DAR" in route:
        recommendations.append("Dar es Salaam route: Monitor port congestion delays.")
    
    if not recommendations:
        recommendations.append("Labor optimization on target. Maintain current staffing levels.")
    
    return recommendations


@router.post("/optimize", response_model=LaborOptimizationResponse)
def optimize_labor(request: LaborOptimizationRequest) -> LaborOptimizationResponse:
    """
    Optimize labor assignments for a route.
    
    **Example:**
    ```json
    {
      "route": "DAR_KAPIRI",
      "work_date": "2026-02-12",
      "required_skills": ["advanced"],
      "shift_type": "day"
    }
    ```
    """
    try:
        # Get optimized assignments
        assignments_data = optimize_labor_assignments(
            request.route,
            request.required_skills,
            request.shift_type
        )
        
        # Convert to response model
        assignments = [DriverAssignment(**a) for a in assignments_data]
        
        # Calculate cost breakdown
        cost_breakdown = calculate_cost_breakdown(assignments_data)
        
        # Calculate totals
        total_drivers = len(assignments)
        total_hours = sum(a.regular_hours + a.overtime_hours for a in assignments)
        overtime_hours = sum(a.overtime_hours for a in assignments)
        avg_efficiency = sum(a.efficiency_score for a in assignments) / len(assignments) if assignments else 0
        
        # Calculate cost savings (vs baseline unoptimized cost)
        baseline_cost = total_hours * 70.0 * 1.2  # Assume 20% inefficiency without optimization
        actual_cost = cost_breakdown["total_cost"]
        cost_savings = max(0, baseline_cost - actual_cost)
        
        # Generate recommendations
        recommendations = generate_recommendations(assignments_data, request.route)
        
        return LaborOptimizationResponse(
            route=request.route,
            work_date=request.work_date,
            assignments=assignments,
            cost_breakdown=LaborCostBreakdown(**cost_breakdown),
            total_drivers=total_drivers,
            total_hours=round(total_hours, 1),
            overtime_hours=round(overtime_hours, 1),
            efficiency_score=round(avg_efficiency, 1),
            cost_savings_zmw=round(cost_savings, 2),
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Labor optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization error: {str(e)}")


@router.get("/status")
def labor_status():
    """Check labor optimization service status."""
    return {
        "service": "operational",
        "version": "1.0",
        "optimization_engine": "active",
        "capabilities": [
            "driver_scheduling",
            "cost_optimization", 
            "skill_matching",
            "overtime_management"
        ]
    }


@router.get("/analytics/drivers")
def get_driver_analytics():
    """Get driver performance analytics."""
    return {
        "total_drivers": 45,
        "available_today": 38,
        "average_efficiency": 82.5,
        "skill_distribution": {
            "advanced": 15,
            "intermediate": 20,
            "basic": 10
        },
        "overtime_trend": "decreasing",
        "cost_trend": "stable"
    }
