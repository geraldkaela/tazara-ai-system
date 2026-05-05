#!/usr/bin/env python3
"""
Debug Multi-route Scheduling Error
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.routes import ROUTES
from reinforcement_rl.train_fleet import TrainFleet
from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv

def debug_environment():
    """Debug the environment initialization"""
    print('🔍 DEBUGGING MULTI-ROUTE ENVIRONMENT')
    print('=' * 50)
    
    print('\n📊 ROUTES INFORMATION:')
    print(f'   Total routes: {len(ROUTES)}')
    print(f'   Route names: {list(ROUTES.keys())}')
    
    print('\n🚂 TRAIN FLEET INFORMATION:')
    fleet = TrainFleet()
    summary = fleet.get_fleet_summary()
    print(f'   Total trains: {summary["total_trains"]}')
    print(f'   Total capacity: {summary["total_capacity"]:,} tons')
    
    print('\n🔧 ENVIRONMENT INITIALIZATION TEST:')
    
    # Test with small cargo requirements
    cargo_requirements = {
        'DAR_KAPIRI': 500,
        'DAR_MBEYA': 200,
        'KAPIRI_NDOLA': 100
    }
    
    print(f'   Cargo requirements: {cargo_requirements}')
    print(f'   Total cargo: {sum(cargo_requirements.values()):,} tons')
    
    try:
        # Initialize environment
        env = MultiRouteTazaraEnv(
            num_trains=3,
            max_cargo=2000,
            cargo_requirements=cargo_requirements
        )
        
        print(f'   ✅ Environment initialized successfully')
        print(f'   Total trains: {env.total_trains}')
        print(f'   Route names: {env.route_names}')
        print(f'   Action space: {env.action_space}')
        print(f'   Observation space: {env.observation_space}')
        
        # Test reset
        print('\n🔄 TESTING ENVIRONMENT RESET:')
        state, info = env.reset()
        print(f'   ✅ Environment reset successful')
        print(f'   State shape: {state.shape}')
        print(f'   Initial cargo: {env.current_cargo}')
        
        # Test step with valid actions
        print('\n⚡ TESTING ENVIRONMENT STEP:')
        actions = [1, 2, 3]  # Valid actions for 3 trains
        print(f'   Actions: {actions}')
        
        next_state, reward, done, truncated, info = env.step(actions)
        print(f'   ✅ Step successful')
        print(f'   Reward: {reward}')
        print(f'   Done: {done}')
        print(f'   Info: {info}')
        
        print('\n🚆 TRAIN INFORMATION:')
        for i, train in enumerate(env.trains):
            print(f'   Train {i}: ID={train.get("train_id", "N/A")}, Capacity={train.get("capacity_tons", "N/A")} tons')
        
    except Exception as e:
        print(f'   ❌ Error: {e}')
        import traceback
        traceback.print_exc()

def debug_agent():
    """Debug the agent loading"""
    print('\n\n🤖 DEBUGGING AGENT LOADING')
    print('=' * 50)
    
    try:
        from reinforcement_rl.multi_route_agent import MultiRouteAgent
        from reinforcement_rl.routes import ROUTES
        
        num_routes = len(ROUTES)
        action_size = num_routes + 1
        
        print(f'   Number of routes: {num_routes}')
        print(f'   Action size: {action_size}')
        
        # Test agent creation
        agent = MultiRouteAgent(
            state_bins=(10,) * 30,
            action_size=action_size
        )
        
        print(f'   ✅ Agent created successfully')
        print(f'   Action size: {agent.action_size}')
        print(f'   Q-table size: {len(agent.q_table)}')
        
        # Test action selection
        import numpy as np
        state = np.random.random(30)  # Dummy state
        actions = agent.select_action(state)
        print(f'   ✅ Action selection successful')
        print(f'   Selected actions: {actions}')
        print(f'   Action range: 0 to {action_size-1}')
        
    except Exception as e:
        print(f'   ❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_environment()
    debug_agent()
