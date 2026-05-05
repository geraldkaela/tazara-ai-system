"""
Geographic Dispatch Optimizer for TAZARA
Phase 4: Intelligent Resource Allocation
"""

import numpy as np
from typing import List, Dict, Tuple, Optional

# Route distances (approx km)
ROUTE_DISTANCES = {
    "DAR_KAPIRI": 1860,
    "DAR_MBEYA": 850,
    "KAPIRI_NDOLA": 200
}

# Regional fuel costs (ZMW per liter)
REGIONAL_FUEL_RATES = {
    "DAR_ES_SALAAM": 25.5,
    "MBEYA": 27.2,
    "KAPIRI_MPOSHI": 28.5,
    "NDOLA": 29.0
}

class GeographicOptimizer:
    """
    Optimizes asset deployment based on geographic constraints and fuel costs.
    """
    def __init__(self):
        pass

    def calculate_fuel_cost(self, route_name: str, train_type: str = "standard") -> float:
        """
        Estimate fuel cost for a route based on distance and regional pricing.
        """
        distance = ROUTE_DISTANCES.get(route_name, 0)
        
        # Consumption rates (liters per km)
        consumption_rates = {
            "standard": 5.2,
            "heavy_cargo": 7.8,
            "efficient": 4.1
        }
        rate = consumption_rates.get(train_type, 5.2)
        total_liters = distance * rate
        
        # Average fuel price based on start node
        if "DAR" in route_name:
            price = REGIONAL_FUEL_RATES["DAR_ES_SALAAM"]
        elif "KAPIRI" in route_name:
            price = REGIONAL_FUEL_RATES["KAPIRI_MPOSHI"]
        else:
            price = 27.0 # Default
            
        return total_liters * price

    def get_geographic_clustering(self, active_trains: List[Dict]) -> List[Dict]:
        """
        Groups trains by geographic proximity to minimize empty "deadhead" runs.
        """
        clusters = {
            "NORTHERN": [], # DAR area
            "CENTRAL": [],  # MBEYA area
            "SOUTHERN": []  # KAPIRI area
        }
        
        for train in active_trains:
            pos = train.get("current_position", "UNKNOWN")
            if pos in ["DAR_ES_SALAAM", "MOROGORO"]:
                clusters["NORTHERN"].append(train)
            elif pos in ["MBEYA", "CHALIMBA"]:
                clusters["CENTRAL"].append(train)
            else:
                clusters["SOUTHERN"].append(train)
                
        return clusters

    def optimize_dispatch_sequence(self, cargo_demands: List[Dict], available_trains: List[Dict]) -> List[Dict]:
        """
        Recommends dispatch order based on nearest-train-first to save fuel.
        """
        recommendations = []
        trains = available_trains.copy()
        
        for demand in cargo_demands:
            origin = demand['origin']
            # Find nearest train (simplified logic)
            best_train = None
            min_dist = float('inf')
            
            for i, train in enumerate(trains):
                # Placeholder for actual geo-distance calculation
                dist = 0 if train['location'] == origin else 500 
                if dist < min_dist:
                    min_dist = dist
                    best_train = i
            
            if best_train is not None:
                t = trains.pop(best_train)
                recommendations.append({
                    "cargo_id": demand['id'],
                    "train_id": t['id'],
                    "est_fuel_cost_zmw": self.calculate_fuel_cost(demand['route'])
                })
                
        return recommendations
