#!/usr/bin/env python3
"""
Debug AI behavior to understand why trains are idle
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent

def debug_universal_agent():
    """Debug why universal agent is not delivering cargo"""
    
    print("DEBUGGING UNIVERSAL AI AGENT")
    print("=" * 60)
    
    try:
        # Load universal agent
        agent = MultiRouteAgent(
            state_bins=(10,) * 20,
            action_size=4
        )
        agent.load('models/multi_route_agent_universal.pkl')
        agent.exploration_rate = 0.0
        
        print("Universal agent loaded successfully")
        
        # Create environment
        env = MultiRouteTazaraEnv(
            num_trains=5,
            max_cargo=5000,
            cargo_requirements={
                "DAR_KAPIRI": 1000,
                "DAR_MBEYA": 1000,
                "KAPIRI_NDOLA": 1000
            }
        )
        
        print(f"Environment created with {env.total_trains} trains")
        print(f"   - Available routes: {list(env.routes.keys())}")
        print(f"   - Initial cargo: {env.current_cargo}")
        
        # Reset environment
        state, _ = env.reset()
        print(f"Initial state shape: {state.shape}")
        
        # Test agent actions for a few steps
        for step in range(5):
            print(f"\n--- Step {step + 1} ---")
            
            # Get agent action
            actions = agent.select_action(state)
            print(f"Agent actions: {actions}")
            
            # Take step
            next_state, reward, done, truncated, info = env.step(actions)
            print(f"Step results:")
            print(f"   - Reward: {reward}")
            print(f"   - Cargo delivered: {sum(env.cargo_delivered.values())}")
            print(f"   - Current cargo: {env.current_cargo}")
            print(f"   - Done: {done}")
            
            state = next_state
            
            if done:
                break
        
        print(f"\nFinal Results:")
        print(f"   - Total cargo delivered: {sum(env.cargo_delivered.values())}")
        print(f"   - Final cargo remaining: {env.current_cargo}")
        
        if sum(env.cargo_delivered.values()) > 0:
            print("SUCCESS: Agent delivered cargo!")
        else:
            print("ISSUE: Agent delivered no cargo")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_universal_agent()
