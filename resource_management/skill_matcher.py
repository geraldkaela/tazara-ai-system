"""
Skill Matching System for TAZARA Resource Management
Phase 4: Intelligent Resource Allocation
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime

class SkillMatcher:
    """
    Matches drivers to train routes based on skill level, experience, and safety records.
    """
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        # Default skill requirements for routes
        self.route_requirements = {
            "DAR_KAPIRI": {"min_level": 3, "required_certs": ["long_haul"]},
            "DAR_MBEYA": {"min_level": 2, "required_certs": ["mountain_pass"]},
            "KAPIRI_NDOLA": {"min_level": 1, "required_certs": ["standard"]}
        }

    def get_optimal_driver(self, route_name: str, available_drivers: List[Dict]) -> Optional[Dict]:
        """
        Find the best driver for a specific route based on multi-criteria scoring.
        """
        requirements = self.route_requirements.get(route_name, {"min_level": 1, "required_certs": []})
        scored_drivers = []

        for driver in available_drivers:
            score = 0
            
            # 1. Level Check (Hard constraint threshold, but higher is better)
            if driver['level'] < requirements['min_level']:
                continue
            score += driver['level'] * 10
            
            # 2. Certification Match
            cert_match = set(requirements['required_certs']).intersection(set(driver.get('certs', [])))
            score += len(cert_match) * 20
            
            # 3. Experience (Total hours)
            score += (driver.get('total_hours', 0) / 100)
            
            # 4. Safety Score (0-100)
            score += driver.get('safety_score', 0) * 0.5
            
            # 5. Last Rest (Fatigue management)
            # Higher days since last shift preferred (simplified)
            score += min(20, driver.get('days_since_last_shift', 0) * 2)

            scored_drivers.append({
                "driver_id": driver['id'],
                "score": score,
                "data": driver
            })

        if not scored_drivers:
            return None

        # Return driver with highest score
        best_match = max(scored_drivers, key=lambda x: x['score'])
        return best_match['data']

    def batch_assign(self, assignments_needed: List[str], available_drivers: List[Dict]) -> Dict[str, str]:
        """
        Assign multiple drivers to routes, optimizing for the whole set.
        Used for weekly schedule planning.
        """
        assignments = {}
        remaining_drivers = available_drivers.copy()

        # Sort assignments by difficulty (min_level requirement)
        sorted_routes = sorted(
            assignments_needed, 
            key=lambda r: self.route_requirements.get(r, {}).get("min_level", 0), 
            reverse=True
        )

        for route in sorted_routes:
            best_driver = self.get_optimal_driver(route, remaining_drivers)
            if best_driver:
                assignments[route] = best_driver['id']
                remaining_drivers = [d for d in remaining_drivers if d['id'] != best_driver['id']]
            else:
                assignments[route] = "UNASSIGNED"

        return assignments

# Example Usage / Test
if __name__ == "__main__":
    drivers = [
        {"id": "DRV001", "level": 4, "certs": ["long_haul", "mountain_pass"], "total_hours": 1200, "safety_score": 98, "days_since_last_shift": 2},
        {"id": "DRV002", "level": 2, "certs": ["standard"], "total_hours": 400, "safety_score": 90, "days_since_last_shift": 5},
        {"id": "DRV003", "level": 3, "certs": ["long_haul"], "total_hours": 800, "safety_score": 95, "days_since_last_shift": 1},
    ]
    
    matcher = SkillMatcher()
    print("Assigning for DAR_KAPIRI (Req Level 3 + long_haul):")
    print(matcher.get_optimal_driver("DAR_KAPIRI", drivers))
    
    print("\nBatch Assignment for ['DAR_KAPIRI', 'DAR_MBEYA']:")
    print(matcher.batch_assign(["DAR_KAPIRI", "DAR_MBEYA"], drivers))
