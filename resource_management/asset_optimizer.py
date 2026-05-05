"""
Asset Utilization and Maintenance Optimizer for TAZARA
Phase 4: Intelligent Resource Allocation
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta

class AssetOptimizer:
    """
    Tracks and optimizes train maintenance schedules and usage buffers.
    """
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        # Maintenance thresholds
        self.max_service_hours = 500  # Hours before service
        self.max_service_days = 30   # Days before service
        
    def check_maintenance_requirement(self, train_id: int, current_status: Dict) -> Dict:
        """
        Check if a train is due for maintenance based on hours and date.
        """
        hours_since_service = current_status.get("hours_since_service", 0)
        last_service_date = current_status.get("last_service_date", datetime.now() - timedelta(days=10))
        days_since_service = (datetime.now() - last_service_date).days
        
        needs_service = (hours_since_service >= self.max_service_hours or 
                        days_since_service >= self.max_service_days)
        
        priority = "LOW"
        if hours_since_service > self.max_service_hours * 1.2:
            priority = "URGENT"
        elif hours_since_service > self.max_service_hours:
            priority = "HIGH"
            
        return {
            "train_id": train_id,
            "needs_service": needs_service,
            "priority": priority,
            "remaining_hours": max(0, self.max_service_hours - hours_since_service),
            "remaining_days": max(0, self.max_service_days - days_since_service)
        }

    def get_utilization_stats(self, schedules: List[Dict]) -> Dict:
        """
        Calculate asset utilization percentage over a period.
        """
        if not schedules:
            return {"avg_utilization": 0}
            
        total_slots = 0
        used_slots = 0
        
        for schedule in schedules:
            num_trains = schedule.get("num_trains", 6)
            total_days = schedule.get("total_days", 14)
            total_slots += num_trains * total_days
            
            # Count non-idle actions
            daily_actions = schedule.get("daily_actions", [])
            for day_actions in daily_actions:
                used_slots += sum(1 for action in day_actions if action > 0)
                
        utilization = (used_slots / total_slots * 100) if total_slots > 0 else 0
        
        return {
            "avg_utilization": utilization,
            "total_slots": total_slots,
            "used_slots": used_slots,
            "efficiency_rating": "OPTIMAL" if 75 <= utilization <= 90 else "SUBOPTIMAL"
        }

    def propose_maintenance_window(self, train_id: int, upcoming_schedules: List[Dict]) -> Optional[str]:
        """
        Suggests a gap in the schedule for maintenance.
        """
        # Logic to find a 2-day gap where the train is idle in the RL schedule
        # Placeholder for complex gap detection
        return "Day 13-14"
