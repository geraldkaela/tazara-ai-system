"""
Baseline Scheduler - Simple heuristic approach for comparison with RL
Uses priority-based scheduling: highest cargo first
"""

from reinforcement_rl.routes import ROUTES
from reinforcement_rl.cost_model import get_cost_breakdown

class BaselineScheduler:
    """
    Rule-based baseline scheduler (no learning) – Phase 2 multi-route.
    Enhanced with ZMW cost tracking for comparison with RL.
    """

    def __init__(self, num_trains=5, max_days=7):
        self.num_trains = num_trains
        self.max_days = max_days
        self.routes = ROUTES
        self.route_names = list(self.routes.keys())
    
    def select_action(self, route_cargo, available_trains):
        """
        Action space:
        0..N-1 = assign train to route i
        N = delay
        N+1 = skip
        """
        # Try to assign a train to a route with cargo
        for i, cargo in enumerate(route_cargo):
            if cargo > 0 and available_trains > 0:
                return i  # assign train to this route

        # No cargo or no trains → choose idle
        return len(route_cargo) + 1
    
    def simulate_week(self, initial_cargo):
        """
        Simulate a full week with baseline scheduling
        
        Args:
            initial_cargo: Dict of route_name -> cargo_amount
            
        Returns:
            schedule: List of daily actions
            metrics: Performance metrics with ZMW costs
        """
        schedule = []
        available_trains = self.num_trains
        total_cargo_delivered = 0
        trains_used = 0
        delay_days = 0
        idle_days = 0
        
        # Convert to list format for select_action
        route_cargo = [initial_cargo.get(route, 0) for route in self.route_names]
        
        for day in range(self.max_days):
            action = self.select_action(route_cargo, available_trains)
            
            if action < len(self.route_names):
                # Dispatch train to route
                route_name = self.route_names[action]
                schedule.append(route_name)
                route = self.routes[route_name]
                
                # Calculate cargo moved
                cargo_per_train = 50  # Estimated tons per train
                cargo_moved = min(cargo_per_train, route_cargo[action])
                
                # Update state
                route_cargo[action] -= cargo_moved
                total_cargo_delivered += cargo_moved
                available_trains -= 1
                trains_used += 1
                
                # Train returns after travel time
                travel_days = 1 if route_name == "KAPIRI_NDOLA" else 2
                if day + travel_days < self.max_days:
                    available_trains += 1
                    
            elif action == len(self.route_names):
                # Delay
                schedule.append("delay")
                delay_days += 1
                # Increase cargo due to delay (5% penalty)
                route_cargo = [c * 1.05 for c in route_cargo]
            else:
                # Idle
                schedule.append("idle")
                idle_days += 1
        
        # Calculate ZMW metrics
        cost_breakdown = get_cost_breakdown(
            cargo_delivered=total_cargo_delivered,
            trains_used=trains_used,
            delay_days=delay_days,
            idle_days=idle_days
        )
        
        metrics = {
            "total_cargo_delivered": total_cargo_delivered,
            "trains_used": trains_used,
            "delay_days": delay_days,
            "idle_days": idle_days,
            "cost_breakdown_zmw": cost_breakdown,
            "schedule_length": len(schedule),
            "scheduler_type": "Baseline (Priority-Based)"
        }
        
        return schedule, metrics
    
    def get_name(self):
        return "Baseline (Priority-Based)"
