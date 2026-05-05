"""
Train Fleet Management System
Different train types with varying capacities for realistic scheduling
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import random

class TrainType(Enum):
    """Different types of trains in TAZARA fleet"""
    HEAVY_FREIGHT = "heavy_freight"
    STANDARD_FREIGHT = "standard_freight"
    LIGHT_FREIGHT = "light_freight"
    PASSENGER_FREIGHT = "passenger_freight"
    EXPRESS_FREIGHT = "express_freight"

@dataclass
class TrainSpec:
    """Train specifications"""
    train_type: TrainType
    capacity_tons: float
    max_speed_kmh: float
    fuel_efficiency_l_per_100km: float
    operating_cost_zmw_per_day: float
    maintenance_cost_zmw_per_1000km: float
    crew_size: int
    suitable_routes: List[str]
    priority: int  # 1=highest priority, 5=lowest
    availability: float  # 0.0 to 1.0 (reliability factor)
    train_id: str = ""  # Will be set after creation

class TrainFleet:
    """TAZARA Train Fleet Manager"""
    
    def __init__(self):
        self.trains = {}
        self._initialize_fleet()
    
    def _initialize_fleet(self):
        """Initialize TAZARA train fleet with realistic specifications"""
        
        # Heavy Freight Trains - For bulk cargo (copper, coal)
        heavy_freight_specs = [
            {
                "train_id": "TF-001",
                "capacity_tons": 1200,
                "max_speed_kmh": 60,
                "fuel_efficiency_l_per_100km": 4.5,
                "operating_cost_zmw_per_day": 8000,
                "maintenance_cost_zmw_per_1000km": 45,
                "crew_size": 3,
                "suitable_routes": ["DAR_KAPIRI", "DAR_MBEYA", "MBEYA_KASAMA"],
                "priority": 2,
                "availability": 0.95
            },
            {
                "train_id": "TF-002", 
                "capacity_tons": 1000,
                "max_speed_kmh": 65,
                "fuel_efficiency_l_per_100km": 4.2,
                "operating_cost_zmw_per_day": 7500,
                "maintenance_cost_zmw_per_1000km": 42,
                "crew_size": 3,
                "suitable_routes": ["DAR_KAPIRI", "KAPIRI_NDOLA"],
                "priority": 2,
                "availability": 0.92
            }
        ]
        
        # Standard Freight Trains - General purpose
        standard_freight_specs = [
            {
                "train_id": "SF-003",
                "capacity_tons": 800,
                "max_speed_kmh": 75,
                "fuel_efficiency_l_per_100km": 3.8,
                "operating_cost_zmw_per_day": 6000,
                "maintenance_cost_zmw_per_1000km": 35,
                "crew_size": 2,
                "suitable_routes": ["DAR_KAPIRI", "DAR_MBEYA", "KAPIRI_NDOLA", "DAR_KIDATU"],
                "priority": 3,
                "availability": 0.90
            },
            {
                "train_id": "SF-004",
                "capacity_tons": 750,
                "max_speed_kmh": 80,
                "fuel_efficiency_l_per_100km": 3.6,
                "operating_cost_zmw_per_day": 5800,
                "maintenance_cost_zmw_per_1000km": 33,
                "crew_size": 2,
                "suitable_routes": ["DAR_KAPIRI", "KAPIRI_NDOLA", "MBEYA_KASAMA"],
                "priority": 3,
                "availability": 0.88
            },
            {
                "train_id": "SF-005",
                "capacity_tons": 700,
                "max_speed_kmh": 78,
                "fuel_efficiency_l_per_100km": 3.7,
                "operating_cost_zmw_per_day": 5600,
                "maintenance_cost_zmw_per_1000km": 32,
                "crew_size": 2,
                "suitable_routes": ["DAR_MBEYA", "KAPIRI_NDOLA", "DAR_KIDATU"],
                "priority": 3,
                "availability": 0.91
            }
        ]
        
        # Light Freight Trains - For smaller cargo, faster routes
        light_freight_specs = [
            {
                "train_id": "LF-006",
                "capacity_tons": 400,
                "max_speed_kmh": 90,
                "fuel_efficiency_l_per_100km": 3.2,
                "operating_cost_zmw_per_day": 4500,
                "maintenance_cost_zmw_per_1000km": 28,
                "crew_size": 2,
                "suitable_routes": ["DAR_KIDATU", "KIDATU_TRANS_SHIPMENT", "KAPIRI_DISTRIBUTION"],
                "priority": 4,
                "availability": 0.93
            },
            {
                "train_id": "LF-007",
                "capacity_tons": 350,
                "max_speed_kmh": 95,
                "fuel_efficiency_l_per_100km": 3.0,
                "operating_cost_zmw_per_day": 4200,
                "maintenance_cost_zmw_per_1000km": 26,
                "crew_size": 2,
                "suitable_routes": ["DAR_KIDATU", "KIDATU_MAKAMBAKO", "MAKAMBAKO_MBEYA"],
                "priority": 4,
                "availability": 0.89
            }
        ]
        
        # Passenger-Freight Mixed Trains - For mixed cargo
        passenger_freight_specs = [
            {
                "train_id": "PF-008",
                "capacity_tons": 500,
                "max_speed_kmh": 85,
                "fuel_efficiency_l_per_100km": 3.5,
                "operating_cost_zmw_per_day": 5500,
                "maintenance_cost_zmw_per_1000km": 30,
                "crew_size": 3,
                "suitable_routes": ["DAR_KAPIRI", "DAR_MBEYA"],
                "priority": 4,
                "availability": 0.87
            }
        ]
        
        # Express Freight - High priority, time-sensitive cargo
        express_freight_specs = [
            {
                "train_id": "EF-009",
                "capacity_tons": 300,
                "max_speed_kmh": 100,
                "fuel_efficiency_l_per_100km": 2.8,
                "operating_cost_zmw_per_day": 5000,
                "maintenance_cost_zmw_per_1000km": 25,
                "crew_size": 2,
                "suitable_routes": ["DAR_KAPIRI", "KAPIRI_NDOLA"],
                "priority": 1,
                "availability": 0.85
            }
        ]
        
        # Create all train specifications
        all_specs = (
            heavy_freight_specs + 
            standard_freight_specs + 
            light_freight_specs + 
            passenger_freight_specs + 
            express_freight_specs
        )
        
        for spec in all_specs:
            train_type = self._get_train_type_from_id(spec["train_id"])
            # Create TrainSpec without duplicating train_id
            train_spec = TrainSpec(
                train_type=train_type,
                capacity_tons=spec["capacity_tons"],
                max_speed_kmh=spec["max_speed_kmh"],
                fuel_efficiency_l_per_100km=spec["fuel_efficiency_l_per_100km"],
                operating_cost_zmw_per_day=spec["operating_cost_zmw_per_day"],
                maintenance_cost_zmw_per_1000km=spec["maintenance_cost_zmw_per_1000km"],
                crew_size=spec["crew_size"],
                suitable_routes=spec["suitable_routes"],
                priority=spec["priority"],
                availability=spec["availability"]
            )
            # Set train_id separately
            train_spec.train_id = spec["train_id"]
            self.trains[spec["train_id"]] = train_spec
    
    def _get_train_type_from_id(self, train_id: str) -> TrainType:
        """Determine train type from ID prefix"""
        prefix = train_id.split("-")[0]
        type_mapping = {
            "TF": TrainType.HEAVY_FREIGHT,
            "SF": TrainType.STANDARD_FREIGHT,
            "LF": TrainType.LIGHT_FREIGHT,
            "PF": TrainType.PASSENGER_FREIGHT,
            "EF": TrainType.EXPRESS_FREIGHT
        }
        return type_mapping.get(prefix, TrainType.STANDARD_FREIGHT)
    
    def get_available_trains(self, route: str = None, min_capacity: float = 0) -> List[TrainSpec]:
        """Get available trains for a specific route"""
        available_trains = []
        
        for train in self.trains.values():
            # Check if train is suitable for the route
            if route and route not in train.suitable_routes:
                continue
            
            # Check if train meets minimum capacity requirement
            if train.capacity_tons < min_capacity:
                continue
            
            # Check availability (random factor for reliability)
            if random.random() > train.availability:
                continue
            
            available_trains.append(train)
        
        # Sort by priority (lower number = higher priority)
        available_trains.sort(key=lambda t: t.priority)
        
        return available_trains
    
    def get_optimal_trains_for_cargo(self, total_cargo: float, route: str) -> List[TrainSpec]:
        """Get optimal train combination for specific cargo and route"""
        available_trains = self.get_available_trains(route, min_capacity=0)
        
        if not available_trains:
            return []
        
        # Greedy algorithm: use highest capacity suitable trains first
        selected_trains = []
        remaining_cargo = total_cargo
        
        for train in available_trains:
            if remaining_cargo <= 0:
                break
            
            # Use train if it can handle remaining cargo or is the best available
            if train.capacity_tons <= remaining_cargo * 1.2:  # Allow slight overcapacity
                selected_trains.append(train)
                remaining_cargo -= train.capacity_tons
        
        return selected_trains
    
    def get_train_by_id(self, train_id: str) -> Optional[TrainSpec]:
        """Get train specification by ID"""
        return self.trains.get(train_id)
    
    def get_fleet_summary(self) -> Dict:
        """Get fleet summary statistics"""
        fleet_stats = {
            "total_trains": len(self.trains),
            "by_type": {},
            "total_capacity": 0,
            "average_availability": 0,
            "operating_cost_per_day": 0
        }
        
        total_availability = 0
        total_operating_cost = 0
        
        for train in self.trains.values():
            # Count by type
            train_type = train.train_type.value
            if train_type not in fleet_stats["by_type"]:
                fleet_stats["by_type"][train_type] = {"count": 0, "total_capacity": 0}
            
            fleet_stats["by_type"][train_type]["count"] += 1
            fleet_stats["by_type"][train_type]["total_capacity"] += train.capacity_tons
            
            fleet_stats["total_capacity"] += train.capacity_tons
            total_availability += train.availability
            total_operating_cost += train.operating_cost_zmw_per_day
        
        fleet_stats["average_availability"] = total_availability / len(self.trains)
        fleet_stats["operating_cost_per_day"] = total_operating_cost
        
        return fleet_stats
    
    def calculate_transport_cost(self, train_id: str, distance_km: float, days: int) -> float:
        """Calculate transport cost for a specific train"""
        train = self.get_train_by_id(train_id)
        if not train:
            return 0
        
        # Operating cost
        operating_cost = train.operating_cost_zmw_per_day * days
        
        # Fuel cost
        fuel_consumed = (distance_km / 100) * train.fuel_efficiency_l_per_100km
        fuel_cost = fuel_consumed * 30  # ZMW 30 per liter
        
        # Maintenance cost
        maintenance_cost = (distance_km / 1000) * train.maintenance_cost_zmw_per_1000km
        
        # Crew cost
        crew_cost = train.crew_size * 200 * days  # ZMW 200 per crew member per day
        
        total_cost = operating_cost + fuel_cost + maintenance_cost + crew_cost
        
        return total_cost
    
    def get_train_efficiency_score(self, train_id: str, cargo_tons: float, route: str) -> float:
        """Calculate efficiency score for train-cargo-route combination"""
        train = self.get_train_by_id(train_id)
        if not train:
            return 0
        
        # Capacity utilization (closer to full capacity is better)
        utilization = cargo_tons / train.capacity_tons
        utilization_score = min(utilization, 1.0)
        
        # Route suitability (bonus if train is well-suited for route)
        route_suitability = 1.0 if route in train.suitable_routes else 0.7
        
        # Priority (higher priority trains get bonus)
        priority_score = (6 - train.priority) / 5  # Convert to 0-1 scale
        
        # Availability (more reliable trains get bonus)
        availability_score = train.availability
        
        # Combined efficiency score
        efficiency_score = (
            utilization_score * 0.4 +
            route_suitability * 0.3 +
            priority_score * 0.2 +
            availability_score * 0.1
        )
        
        return efficiency_score
