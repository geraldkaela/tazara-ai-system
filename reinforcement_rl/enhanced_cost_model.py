"""
Enhanced Cost Model for TAZARA Multi-Route System
Phase 1: Labor Cost Optimization with Overtime and Idle Time Management
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import numpy as np

# 🚆 ZMW Labor Cost Factors (realistic Zambian rates)
BASE_HOURLY_WAGE_ZMW = 50.0          # Base wage per hour
OVERTIME_MULTIPLIER = 1.5               # 1.5x for overtime
PREMIUM_OVERTIME_MULTIPLIER = 2.0      # 2x for premium overtime (>8 hours/day)
STANDARD_HOURS_PER_DAY = 8.0           # Standard work hours
MAX_OVERTIME_HOURS_PER_DAY = 4.0        # Maximum overtime allowed

# 🚆 Route-specific labor complexity factors
LABOR_COMPLEXITY_FACTORS = {
    "DAR_KAPIRI": 1.2,    # Long route - more complex
    "DAR_MBEYA": 1.1,     # Medium route
    "KAPIRI_NDOLA": 1.0    # Short route - standard
}

# 🚆 Skill-based wage premiums
SKILL_LEVEL_PREMIUMS = {
    "beginner": 0.0,       # Base wage
    "intermediate": 0.2,    # 20% premium
    "advanced": 0.4,        # 40% premium
    "expert": 0.6           # 60% premium
}

# 🚆 Shift differentials
SHIFT_DIFFERENTIALS = {
    "day": 0.0,           # 6:00 - 18:00
    "evening": 0.15,      # 18:00 - 22:00 (15% premium)
    "night": 0.25,        # 22:00 - 6:00 (25% premium)
    "weekend": 0.3        # Weekend work (30% premium)
}

class LaborCostCalculator:
    """Advanced labor cost calculation with overtime and efficiency tracking"""
    
    def __init__(self):
        self.driver_skills = {}  # driver_id -> skill_level
        self.shift_assignments = {}  # driver_id -> shift_type
        self.work_hours = {}  # driver_id -> total_hours_worked
        
    def set_driver_skill(self, driver_id: str, skill_level: str):
        """Set driver skill level for wage calculation"""
        self.driver_skills[driver_id] = skill_level.lower()
    
    def set_driver_shift(self, driver_id: str, shift_type: str):
        """Set driver shift for differential calculation"""
        self.shift_assignments[driver_id] = shift_type.lower()
    
    def calculate_labor_cost(self, 
                          driver_id: str, 
                          hours_worked: float,
                          route_name: str = None,
                          is_weekend: bool = False) -> Dict:
        """
        Calculate comprehensive labor cost including overtime and premiums
        """
        # Get driver-specific factors
        skill_level = self.driver_skills.get(driver_id, "beginner")
        skill_premium = SKILL_LEVEL_PREMIUMS.get(skill_level, 0.0)
        
        shift_type = self.shift_assignments.get(driver_id, "day")
        shift_differential = SHIFT_DIFFERENTIALS.get(shift_type, 0.0)
        
        # Add weekend premium if applicable
        if is_weekend:
            shift_differential = max(shift_differential, SHIFT_DIFFERENTIALS["weekend"])
        
        # Calculate base wage with premiums
        base_hourly_rate = BASE_HOURLY_WAGE_ZMW * (1 + skill_premium + shift_differential)
        
        # Calculate overtime
        regular_hours = min(hours_worked, STANDARD_HOURS_PER_DAY)
        overtime_hours = max(0, hours_worked - STANDARD_HOURS_PER_DAY)
        
        # Calculate premium overtime (beyond 12 hours total)
        premium_overtime_hours = max(0, overtime_hours - MAX_OVERTIME_HOURS_PER_DAY)
        regular_overtime_hours = overtime_hours - premium_overtime_hours
        
        # Calculate costs
        regular_cost = regular_hours * base_hourly_rate
        overtime_cost = regular_overtime_hours * base_hourly_rate * OVERTIME_MULTIPLIER
        premium_overtime_cost = premium_overtime_hours * base_hourly_rate * PREMIUM_OVERTIME_MULTIPLIER
        
        # Apply route complexity factor
        route_factor = LABOR_COMPLEXITY_FACTORS.get(route_name, 1.0)
        
        total_cost = (regular_cost + overtime_cost + premium_overtime_cost) * route_factor
        
        return {
            "driver_id": driver_id,
            "hours_worked": hours_worked,
            "regular_hours": regular_hours,
            "overtime_hours": overtime_hours,
            "premium_overtime_hours": premium_overtime_hours,
            "base_hourly_rate": base_hourly_rate,
            "regular_cost": regular_cost,
            "overtime_cost": overtime_cost,
            "premium_overtime_cost": premium_overtime_cost,
            "route_factor": route_factor,
            "total_labor_cost_zmw": total_cost,
            "skill_level": skill_level,
            "shift_type": shift_type,
            "is_weekend": is_weekend
        }
    
    def calculate_team_labor_cost(self, 
                               driver_assignments: List[Dict],
                               route_name: str = None) -> Dict:
        """
        Calculate labor cost for entire team
        """
        team_costs = []
        total_cost = 0
        total_hours = 0
        total_overtime = 0
        
        for assignment in driver_assignments:
            driver_id = assignment["driver_id"]
            hours = assignment["hours_worked"]
            
            cost_breakdown = self.calculate_labor_cost(
                driver_id=driver_id,
                hours_worked=hours,
                route_name=route_name,
                is_weekend=assignment.get("is_weekend", False)
            )
            
            team_costs.append(cost_breakdown)
            total_cost += cost_breakdown["total_labor_cost_zmw"]
            total_hours += hours
            total_overtime += cost_breakdown["overtime_hours"] + cost_breakdown["premium_overtime_hours"]
        
        return {
            "team_costs": team_costs,
            "total_team_cost_zmw": total_cost,
            "total_hours_worked": total_hours,
            "total_overtime_hours": total_overtime,
            "average_cost_per_hour": total_cost / total_hours if total_hours > 0 else 0,
            "overtime_percentage": (total_overtime / total_hours * 100) if total_hours > 0 else 0
        }

class IdleTimeOptimizer:
    """Optimize driver assignments to minimize idle time"""
    
    def __init__(self):
        self.driver_availability = {}  # driver_id -> available_hours
        self.task_requirements = {}     # task_id -> required_hours, skill_level
        
    def set_driver_availability(self, driver_id: str, available_hours: float):
        """Set driver available hours"""
        self.driver_availability[driver_id] = available_hours
    
    def add_task_requirement(self, task_id: str, required_hours: float, skill_level: str = "beginner"):
        """Add task with skill requirement"""
        self.task_requirements[task_id] = {
            "required_hours": required_hours,
            "skill_level": skill_level,
            "assigned_driver": None
        }
    
    def optimize_assignments(self) -> Dict:
        """
        Optimize driver assignments to minimize idle time
        Returns assignment plan with efficiency metrics
        """
        assignments = {}
        total_idle_time = 0
        total_utilization = 0
        
        # Sort tasks by required hours (largest first for better fit)
        sorted_tasks = sorted(self.task_requirements.items(), 
                           key=lambda x: x[1]["required_hours"], reverse=True)
        
        for task_id, task_info in sorted_tasks:
            best_driver = None
            min_waste = float('inf')
            
            # Find driver with best fit (minimum idle time)
            for driver_id, available_hours in self.driver_availability.items():
                if available_hours >= task_info["required_hours"]:
                    waste = available_hours - task_info["required_hours"]
                    if waste < min_waste:
                        min_waste = waste
                        best_driver = driver_id
            
            if best_driver:
                assignments[task_id] = {
                    "driver_id": best_driver,
                    "required_hours": task_info["required_hours"],
                    "available_hours": self.driver_availability[best_driver],
                    "idle_hours": min_waste,
                    "utilization": (task_info["required_hours"] / self.driver_availability[best_driver]) * 100
                }
                
                # Update driver availability
                self.driver_availability[best_driver] -= task_info["required_hours"]
                total_idle_time += min_waste
                total_utilization += assignments[task_id]["utilization"]
        
        return {
            "assignments": assignments,
            "total_idle_time": total_idle_time,
            "average_utilization": total_utilization / len(assignments) if assignments else 0,
            "optimization_efficiency": 100 - (total_idle_time / sum(self.driver_availability.values()) * 100) if self.driver_availability else 0
        }

def calculate_labor_efficiency_metrics(labor_costs: List[Dict]) -> Dict:
    """
    Calculate comprehensive labor efficiency metrics
    """
    if not labor_costs:
        return {}
    
    total_cost = sum(cost["total_labor_cost_zmw"] for cost in labor_costs)
    total_hours = sum(cost["hours_worked"] for cost in labor_costs)
    total_overtime = sum(cost["overtime_hours"] + cost["premium_overtime_hours"] for cost in labor_costs)
    
    efficiency_metrics = {
        "total_labor_cost_zmw": total_cost,
        "total_hours_worked": total_hours,
        "total_overtime_hours": total_overtime,
        "average_cost_per_hour": total_cost / total_hours if total_hours > 0 else 0,
        "overtime_percentage": (total_overtime / total_hours * 100) if total_hours > 0 else 0,
        "labor_cost_efficiency": 100 - (total_overtime / total_hours * 50) if total_hours > 0 else 100,  # Penalty for overtime
        "cost_distribution": {
            "regular_hours_cost": sum(cost["regular_cost"] for cost in labor_costs),
            "overtime_cost": sum(cost["overtime_cost"] for cost in labor_costs),
            "premium_overtime_cost": sum(cost["premium_overtime_cost"] for cost in labor_costs)
        }
    }
    
    return efficiency_metrics

# Test the enhanced cost model
if __name__ == "__main__":
    # Initialize calculator
    calculator = LaborCostCalculator()
    
    # Set up drivers with different skills and shifts
    calculator.set_driver_skill("driver_001", "advanced")
    calculator.set_driver_skill("driver_002", "intermediate")
    calculator.set_driver_skill("driver_003", "beginner")
    
    calculator.set_driver_shift("driver_001", "day")
    calculator.set_driver_shift("driver_002", "night")
    calculator.set_driver_shift("driver_003", "evening")
    
    # Calculate costs for different scenarios
    print("🚆 Enhanced Labor Cost Model Test")
    print("=" * 50)
    
    # Test individual driver costs
    driver_cost = calculator.calculate_labor_cost(
        driver_id="driver_001",
        hours_worked=10.5,  # 2.5 hours overtime
        route_name="DAR_KAPIRI",
        is_weekend=False
    )
    
    print(f"Driver 001 Cost Breakdown:")
    print(f"  Regular Hours: {driver_cost['regular_hours']:.1f} @ ZMW {driver_cost['base_hourly_rate']:.2f}/hr")
    print(f"  Overtime Hours: {driver_cost['overtime_hours']:.1f} @ {OVERTIME_MULTIPLIER}x")
    print(f"  Premium Overtime: {driver_cost['premium_overtime_hours']:.1f} @ {PREMIUM_OVERTIME_MULTIPLIER}x")
    print(f"  Total Labor Cost: ZMW {driver_cost['total_labor_cost_zmw']:.2f}")
    print(f"  Skill Premium: {driver_cost['skill_level']} (+{SKILL_LEVEL_PREMIUMS[driver_cost['skill_level']]*100:.0f}%)")
    print(f"  Shift Differential: {driver_cost['shift_type']} (+{SHIFT_DIFFERENTIALS[driver_cost['shift_type']]*100:.0f}%)")
    print()
    
    # Test team cost calculation
    team_assignments = [
        {"driver_id": "driver_001", "hours_worked": 10.5, "is_weekend": False},
        {"driver_id": "driver_002", "hours_worked": 8.0, "is_weekend": True},
        {"driver_id": "driver_003", "hours_worked": 12.0, "is_weekend": False}
    ]
    
    team_cost = calculator.calculate_team_labor_cost(team_assignments, "DAR_KAPIRI")
    
    print("Team Cost Summary:")
    print(f"  Total Team Cost: ZMW {team_cost['total_team_cost_zmw']:.2f}")
    print(f"  Total Hours: {team_cost['total_hours_worked']:.1f}")
    print(f"  Overtime Percentage: {team_cost['overtime_percentage']:.1f}%")
    print(f"  Average Cost/Hour: ZMW {team_cost['average_cost_per_hour']:.2f}")
    print()
    
    # Test idle time optimization
    optimizer = IdleTimeOptimizer()
    optimizer.set_driver_availability("driver_001", 8.0)
    optimizer.set_driver_availability("driver_002", 8.0)
    optimizer.set_driver_availability("driver_003", 6.0)
    
    optimizer.add_task_requirement("task_001", 4.0, "intermediate")
    optimizer.add_task_requirement("task_002", 6.0, "beginner")
    optimizer.add_task_requirement("task_003", 3.0, "advanced")
    
    optimization_result = optimizer.optimize_assignments()
    
    print("Idle Time Optimization Results:")
    print(f"  Average Utilization: {optimization_result['average_utilization']:.1f}%")
    print(f"  Total Idle Time: {optimization_result['total_idle_time']:.1f} hours")
    print(f"  Optimization Efficiency: {optimization_result['optimization_efficiency']:.1f}%")
    
    for task_id, assignment in optimization_result['assignments'].items():
        print(f"  {task_id}: Driver {assignment['driver_id']} - {assignment['utilization']:.1f}% utilization")
