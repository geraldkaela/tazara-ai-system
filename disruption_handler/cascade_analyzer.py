"""
Cascade Effect Analyzer for TAZARA Disruption Handling
Phase 3: Robust Disruption Handling
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta

class CascadeAnalyzer:
    """
    Analyzes how a single disruption propagates through the train schedule.
    """
    def __init__(self):
        pass

    def analyze_delay_propagation(self, 
                                 original_schedule: List[Dict], 
                                 disrupted_train_id: int, 
                                 delay_days: int, 
                                 start_day: int) -> Dict:
        """
        Calculates the ripple effect of a delay on subsequent assignments.
        """
        impacts = []
        total_delay_ripples = 0
        affected_drivers = set()
        
        # 1. Direct Impact
        direct_impact = {
            "train_id": disrupted_train_id,
            "day": start_day,
            "type": "DIRECT",
            "delay": delay_days,
            "description": f"Train {disrupted_train_id} delayed by {delay_days} days starting Day {start_day}"
        }
        impacts.append(direct_impact)
        
        # 2. Sequential Cascade (Same Train)
        # If Train 1 is delayed, its next mission is pushed back
        current_train_delay = delay_days
        for assignment in original_schedule:
            if assignment['train_id'] == disrupted_train_id and assignment['day'] > start_day:
                impacts.append({
                    "train_id": disrupted_train_id,
                    "day": assignment['day'],
                    "type": "SEQUENTIAL",
                    "delay": current_train_delay,
                    "description": f"Subsequent mission for Train {disrupted_train_id} pushed back"
                })
                total_delay_ripples += current_train_delay
        
        # 3. Labor Cascade (Driver shifts)
        # If Driver X was on the delayed train, their next shift on ANY train is at risk
        disrupted_assignment = next((a for a in original_schedule if a['train_id'] == disrupted_train_id and a['day'] == start_day), None)
        if disrupted_assignment and 'driver_id' in disrupted_assignment:
            driver_id = disrupted_assignment['driver_id']
            affected_drivers.add(driver_id)
            
            for assignment in original_schedule:
                if assignment.get('driver_id') == driver_id and assignment['day'] > start_day:
                    impacts.append({
                        "train_id": assignment['train_id'],
                        "day": assignment['day'],
                        "type": "LABOR_CONFLICT",
                        "driver_id": driver_id,
                        "description": f"Driver {driver_id} availability conflict for Train {assignment['train_id']}"
                    })
        
        # 4. Route Congestion (Simplified)
        # If multiple trains arrive at the same terminal simultaneously due to delay
        # (This is a placeholder for more complex logic)
        
        return {
            "disruption_summary": {
                "initial_delay": delay_days,
                "total_ripple_days": total_delay_ripples,
                "affected_trains_count": len(set(i['train_id'] for i in impacts)),
                "affected_drivers_count": len(affected_drivers)
            },
            "cascade_events": impacts,
            "severity_score": (delay_days * 2) + total_delay_ripples + (len(affected_drivers) * 5)
        }

    def identify_critical_bottlenecks(self, schedule: List[Dict]) -> List[Dict]:
        """
        Identifies assignments that, if delayed, would cause the most cascade damage.
        """
        bottlenecks = []
        # Sensitivity analysis: simulated 1-day delay for each assignment
        for train_id in range(6): # Assuming 6 trains
            impact = self.analyze_delay_propagation(schedule, train_id, 1, 1)
            if impact['severity_score'] > 15: # Arbitrary threshold
                bottlenecks.append({
                    "train_id": train_id,
                    "sensitivity": impact['severity_score'],
                    "type": "HIGH_UTILIZATION_ASSET"
                })
        
        return sorted(bottlenecks, key=lambda x: x['sensitivity'], reverse=True)
