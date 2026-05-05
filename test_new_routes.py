#!/usr/bin/env python3
"""
Test the new TAZARA route system
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.routes import ROUTES

def test_new_routes():
    """Test the expanded TAZARA route system"""
    
    print("TESTING EXPANDED TAZARA ROUTE SYSTEM")
    print("=" * 50)
    
    print(f"Total routes available: {len(ROUTES)}")
    print("Routes:")
    for i, route_name in enumerate(ROUTES.keys()):
        route = ROUTES[route_name]
        print(f"  {i+1}. {route_name} - {route.route_type} - {route.region}")
        print(f"     Stations: {', '.join(route.stations)}")
        print(f"     Distance: {route.distance_km}km, Time: {route.travel_hours}h")
    
    print(f"\n" + "=" * 50)
    print("TESTING ENVIRONMENT WITH NEW ROUTES")
    
    try:
        # Test with a simple scenario
        env = MultiRouteTazaraEnv(
            num_trains=3,
            max_cargo=5000,
            cargo_requirements={
                "DAR_KAPIRI": 500,
                "DAR_MBEYA": 300,
                "KAPIRI_NDOLA": 200
            }
        )
        
        print(f"Environment created successfully")
        print(f"Action space: {env.action_space}")
        print(f"Observation space: {env.observation_space}")
        print(f"Route names: {env.route_names}")
        
        # Test reset
        state, _ = env.reset()
        print(f"State shape: {state.shape}")
        print(f"Initial cargo: {env.current_cargo}")
        
        # Test a simple action
        action = [1, 2, 3]  # Use first 3 routes
        print(f"Testing action: {action}")
        
        next_state, reward, done, truncated, info = env.step(action)
        print(f"Step successful - Reward: {reward}, Done: {done}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_routes()
