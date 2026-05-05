import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import List, Dict, Tuple, Optional

from forecasting.predict_cargo import predict_cargo
from reinforcement_rl.routes import ROUTES
from reinforcement_rl.improved_cost_model import (
    dispatch_reward,
    train_usage_penalty,
    delay_penalty,
    idle_penalty,
    coordination_bonus,
    get_improved_cost_breakdown
)
from reinforcement_rl.train_fleet import TrainFleet, TrainType

# 🚆 Route travel times (days) - Updated for TAZARA network
ROUTE_TRAVEL_DAYS = {
    # Main Through Traffic Routes
    "DAR_KAPIRI": 3,  # 72 hours = 3 days
    "DAR_MBEYA": 1.5,  # 36 hours = 1.5 days
    "KAPIRI_NDOLA": 0.75,  # 18 hours = 0.75 days
    
    # Tanzania Local Routes
    "DAR_KIDATU": 0.33,  # 8 hours = 0.33 days
    "KIDATU_MAKAMBAKO": 0.58,  # 14 hours = 0.58 days
    "MAKAMBAKO_MBEYA": 0.58,  # 14 hours = 0.58 days
    
    # Cross-Border Routes
    "MBEYA_KASAMA": 1.33,  # 32 hours = 1.33 days
    
    # Zambia Local Routes
    "KASAMA_MPIKA": 0.5,  # 12 hours = 0.5 days
    "MPIKA_SERENJE": 0.33,  # 8 hours = 0.33 days
    "SERENJE_KAPIRI": 0.25,  # 6 hours = 0.25 days
    
    # Special Routes
    "KIDATU_TRANS_SHIPMENT": 0.17,  # 4 hours = 0.17 days
    "KAPIRI_DISTRIBUTION": 0.83,  # 20 hours = 0.83 days
}

# 🚆 Train states
TRAIN_STATES = {
    "IDLE": 0,
    "EN_ROUTE": 1,
    "LOADING": 2,
    "UNLOADING": 3
}


class MultiRouteTazaraEnv(gym.Env):
    """
    Multi-route TAZARA environment with parallel train operations
    Phase 2 – Multi-route scheduling
    """

    metadata = {"render_modes": ["human"]}

    def __init__(self, num_trains=6, max_cargo=5000, feature_template=None, cargo_requirements=None):
        super().__init__()

        self.total_trains = num_trains
        self.max_cargo = max_cargo
        self.routes = ROUTES
        self.route_names = list(self.routes.keys())
        
        # Initialize train fleet system
        self.train_fleet = TrainFleet()
        
        # Store cargo requirements for use in reset()
        self.cargo_requirements = cargo_requirements or {}
        
        # Default cargo types for routes (can be overridden)
        self.default_cargo_types = {
            "DAR_KAPIRI": "Copper",      # High-value mineral route
            "DAR_MBEYA": "Containers",   # Commercial cargo
            "MBEYA_KASAMA": "Coal",      # Bulk cargo
            "KAPIRI_NDOLA": "Fuel",      # Fuel distribution
            "DAR_KIDATU": "Other",       # Mixed cargo
            "KIDATU_TRANS_SHIPMENT": "Containers"  # Trans-shipment
        }

        self.feature_template = feature_template or {
            f"feature{i}": 0 for i in range(1, 14)
        }

        # Enhanced state: [cargo_route_1, cargo_route_2, ..., train_1_state, train_1_route, train_1_time_left, ..., train_n_state, train_n_route, train_n_time_left, available_trains]
        # Each train: state (0-3), route (-1=idle), time_left (days remaining)
        obs_size = len(self.routes) + (self.total_trains * 3) + 1

        self.observation_space = spaces.Box(
            low=-1,  # Allow -1 for idle trains
            high=max_cargo,
            shape=(obs_size,),
            dtype=np.float32
        )

        # Enhanced action space: For each train, choose route or idle
        # Actions: [train_1_action, train_2_action, ..., train_n_action]
        # Each action: 0=idle, 1=DAR_KAPIRI, 2=DAR_MBEYA, 3=KAPIRI_NDOLA
        self.action_space = spaces.MultiDiscrete(
            [len(self.route_names) + 1] * self.total_trains
        )

        # Initialize environment state
        self.reset_state()

    def reset_state(self):
        """Reset all environment variables with train fleet integration"""
        self.current_cargo = {route: 0 for route in self.route_names}
        self.available_trains = self.total_trains
        
        # Multi-train tracking with train fleet
        self.trains = []
        
        # Get optimal trains for current cargo requirements
        total_cargo = sum(self.cargo_requirements.values()) if self.cargo_requirements else 1000
        
        # Select trains based on cargo requirements and routes
        selected_trains = []
        for route, cargo_amount in self.cargo_requirements.items():
            if cargo_amount > 0:
                route_trains = self.train_fleet.get_optimal_trains_for_cargo(cargo_amount, route)
                selected_trains.extend(route_trains)
        
        # If no specific trains selected, use available fleet
        if not selected_trains:
            all_available = self.train_fleet.get_available_trains()
            selected_trains = all_available[:self.total_trains]
        
        # Initialize trains with fleet specifications
        for i, train_spec in enumerate(selected_trains[:self.total_trains]):
            self.trains.append({
                'id': i,
                'train_id': train_spec.train_id,
                'train_spec': train_spec,
                'state': TRAIN_STATES["IDLE"],
                'route': -1,  # -1 means idle
                'time_left': 0,
                'cargo_carried': 0,
                'capacity_tons': train_spec.capacity_tons
            })
        
        # Fill remaining slots with generic trains if needed
        while len(self.trains) < self.total_trains:
            self.trains.append({
                'id': len(self.trains),
                'train_id': f"GEN-{len(self.trains)+1:03d}",
                'train_spec': None,
                'state': TRAIN_STATES["IDLE"],
                'route': -1,
                'time_left': 0,
                'cargo_carried': 0,
                'capacity_tons': 500  # Default capacity
            })
        
        self.day = 0
        self.total_reward = 0
        self.cargo_delivered = {route: 0 for route in self.route_names}
        self.cargo_types_delivered = {route: [] for route in self.route_names}
        self.total_trains_used = 0
        self.delay_days = 0
        self.idle_days = 0

    def reset(self, seed=None, options=None):
        """Reset environment to initial state"""
        super().reset(seed=seed)
        
        self.reset_state()
        
        # Initialize cargo from forecasting
        # Use user-provided cargo requirements if available
        if self.cargo_requirements:
            for route_name in self.route_names:
                self.current_cargo[route_name] = min(self.cargo_requirements.get(route_name, 0), self.max_cargo)
                # Initialize cargo types list for this route
                cargo_amount = self.cargo_requirements.get(route_name, 0)
                if cargo_amount > 0:
                    # For now, use default cargo type - in future, this could come from order data
                    cargo_type = self.default_cargo_types.get(route_name, "Other")
                    self.cargo_types_delivered[route_name] = [cargo_type] * int(cargo_amount / 100)  # Track by 100-ton units
        else:
            # Fall back to forecasting if no user input
            for route_name in self.route_names:
                # Create input data for prediction
                input_data = {
                    'route': route_name,
                    **self.feature_template
                }
                predicted_cargo = predict_cargo(input_data)
                self.current_cargo[route_name] = min(predicted_cargo, self.max_cargo)
            self.current_cargo[route_name] = min(predicted_cargo, self.max_cargo)
        
        return self._get_state(), {}

    def _get_state(self) -> np.ndarray:
        """Get current state representation"""
        state = []
        
        # Cargo levels for each route
        for route_name in self.route_names:
            state.append(self.current_cargo[route_name])
        
        # Train states: each train contributes 3 values
        for train in self.trains:
            state.append(train['state'])  # 0=idle, 1=en_route, 2=loading, 3=unloading
            state.append(train['route'])   # -1=idle, 0=route_0, 1=route_1, 2=route_2
            state.append(train['time_left'])  # days remaining
        
        # Available trains count
        state.append(self.available_trains)
        
        return np.array(state, dtype=np.float32)

    def step(self, actions: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """Execute one time step with multi-train actions"""
        self.day += 1
        step_reward = 0
        step_info = {}
        
        # Process each train's action
        active_trains = 0
        for i, action in enumerate(actions):
            train = self.trains[i]
            
            if action == 0:  # Idle
                if train['state'] == TRAIN_STATES["IDLE"]:
                    step_reward += idle_penalty(self.idle_days, active_trains)
                    self.idle_days += 1
            else:  # Assign to route
                route_idx = action - 1
                route_name = self.route_names[route_idx]
                
                if train['state'] == TRAIN_STATES["IDLE"] and self.current_cargo[route_name] > 0:
                    # Check if train is suitable for this route
                    if train['train_spec'] and route_name not in train['train_spec'].suitable_routes:
                        # Train not suitable for this route, apply penalty
                        step_reward -= 100  # Penalty for using unsuitable train
                        continue
                    
                    # Assign train to route
                    train['state'] = TRAIN_STATES["EN_ROUTE"]
                    train['route'] = route_idx
                    train['time_left'] = ROUTE_TRAVEL_DAYS[route_name]
                    
                    # Calculate cargo moved based on train capacity
                    train_capacity = train.get('capacity_tons', 500)
                    route = self.routes[route_name]  # Use route_name instead of route_idx
                    
                    # Consider train capacity and route constraints
                    max_cargo_by_train = train_capacity
                    max_cargo_by_route = self.current_cargo[route_name]
                    cargo_moved = min(max_cargo_by_train, max_cargo_by_route)
                    
                    # Apply efficiency factor based on train-cargo match
                    if train['train_spec']:
                        efficiency_score = self.train_fleet.get_train_efficiency_score(
                            train['train_id'], cargo_moved, route_name
                        )
                        cargo_moved *= efficiency_score
                    
                    train['cargo_carried'] = cargo_moved
                    self.current_cargo[route_name] -= cargo_moved
                    
                    # Get cargo type for this route
                    cargo_type = self.default_cargo_types.get(route_name, "Other")
                    step_reward += dispatch_reward(cargo_moved, route_name, cargo_type)
                    self.cargo_delivered[route_name] += cargo_moved
                    self.total_trains_used += 1
                    self.available_trains -= 1
                    active_trains += 1
        
        # Update train positions and handle arrivals
        for train in self.trains:
            if train['state'] == TRAIN_STATES["EN_ROUTE"]:
                train['time_left'] -= 1
                
                if train['time_left'] <= 0:
                    # Train arrives at destination
                    train['state'] = TRAIN_STATES["UNLOADING"]
                    train['time_left'] = 1  # Unloading takes 1 day
                    
            elif train['state'] == TRAIN_STATES["UNLOADING"]:
                train['time_left'] -= 1
                
                if train['time_left'] <= 0:
                    # Train becomes available again
                    train['state'] = TRAIN_STATES["IDLE"]
                    train['route'] = -1
                    train['cargo_carried'] = 0
                    self.available_trains += 1
        
        # Apply operational costs
        step_reward += train_usage_penalty(self.total_trains_used)
        step_reward += delay_penalty(self.delay_days)
        step_reward += idle_penalty(self.idle_days, active_trains)
        
        # Add coordination bonus for multi-train operations
        step_reward += coordination_bonus(active_trains, self.total_trains)
        
        self.total_reward += step_reward
        
        # Check termination conditions
        done = self._is_done()
        truncated = False
        
        # Additional info
        step_info = {
            'day': self.day,
            'total_reward': self.total_reward,
            'cargo_delivered': self.cargo_delivered,
            'trains_used': self.total_trains_used,
            'available_trains': self.available_trains,
            'train_states': self.trains
        }
        
        return self._get_state(), step_reward, done, truncated, step_info

    def _is_done(self) -> bool:
        """Check if episode should terminate"""
        # Terminate if all cargo delivered or max days reached
        total_cargo_remaining = sum(self.current_cargo.values())
        return total_cargo_remaining == 0 or self.day >= 14  # 2 weeks max

    def render(self):
        """Render current environment state"""
        print(f"\n🚂 Day {self.day}")
        print(f"📦 Cargo Remaining: {self.current_cargo}")
        print(f"🚊 Available Trains: {self.available_trains}/{self.total_trains}")
        print(f"💰 Total Reward: {self.total_reward:.2f}")
        
        print("\n🚆 Train Status:")
        for train in self.trains:
            status = "IDLE"
            if train['state'] == TRAIN_STATES["EN_ROUTE"]:
                status = f"EN_ROUTE ({self.route_names[train['route']]}, {train['time_left']} days)"
            elif train['state'] == TRAIN_STATES["UNLOADING"]:
                status = f"UNLOADING ({train['time_left']} days)"
            
            print(f"  Train {train['id']}: {status}")

    def get_performance_metrics(self) -> Dict:
        """Get detailed performance metrics"""
        total_cargo_delivered = sum(self.cargo_delivered.values())
        active_trains = sum(1 for t in self.trains if t['state'] != TRAIN_STATES["IDLE"])
        
        # Calculate improved cost breakdown
        # Determine primary route and cargo type for cost analysis
        primary_route = max(self.cargo_delivered.keys(), key=lambda k: self.cargo_delivered[k]) if self.cargo_delivered else "DAR_KAPIRI"
        primary_cargo_type = self.default_cargo_types.get(primary_route, "Other")
        
        cost_breakdown = get_improved_cost_breakdown(
            cargo_delivered=total_cargo_delivered,
            trains_used=self.total_trains_used,
            delay_days=self.delay_days,
            idle_days=self.idle_days,
            active_trains=active_trains,
            route_name=primary_route,
            cargo_type=primary_cargo_type
        )
        
        return {
            'total_cargo_delivered': total_cargo_delivered,
            'trains_used': self.total_trains_used,
            'active_trains': active_trains,
            'delay_days': self.delay_days,
            'idle_days': self.idle_days,
            'total_reward': self.total_reward,
            'days_completed': self.day,
            'efficiency': total_cargo_delivered / max(self.total_trains_used, 1),
            'cost_breakdown_zmw': cost_breakdown
        }
