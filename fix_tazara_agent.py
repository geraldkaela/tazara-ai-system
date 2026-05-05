#!/usr/bin/env python3
"""
Quick fix for TAZARA agent to try work actions
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent

def fix_tazara_agent():
    """Force TAZARA agent to try work actions"""
    
    print("FIXING TAZARA NETWORK AGENT")
    print("=" * 40)
    
    # Load the existing agent
    agent = MultiRouteAgent(
        state_bins=(10,) * 30,
        action_size=13
    )
    agent.load('models/multi_route_agent_tazara_network.pkl')
    agent.exploration_rate = 0.0
    
    # Create test environment
    env = MultiRouteTazaraEnv(
        num_trains=8,
        max_cargo=5000,
        cargo_requirements={
            "DAR_KAPIRI": 1000,
            "DAR_MBEYA": 800,
            "MBEYA_KASAMA": 600,
            "DAR_KIDATU": 400
        }
    )
    
    print(f"Available routes with cargo: {[k for k, v in env.current_cargo.items() if v > 0]}")
    print(f"Route indices: {list(env.route_names).index('DAR_KAPIRI') + 1} for DAR_KAPIRI")
    
    # Force work actions and update Q-table
    state, _ = env.reset()
    
    # Try different work actions
    work_scenarios = [
        [1, 2, 3, 4, 5, 0, 0, 0],  # Mix of first 5 routes
        [1, 1, 1, 1, 1, 1, 1, 1],  # All DAR_KAPIRI
        [2, 2, 2, 2, 2, 2, 2, 2],  # All DAR_MBEYA
        [3, 3, 3, 3, 3, 3, 3, 3],  # All KAPIRI_NDOLA
        [7, 7, 7, 7, 7, 7, 7, 7],  # All MBEYA_KASAMA
    ]
    
    for i, actions in enumerate(work_scenarios):
        print(f"\nTesting scenario {i+1}: {actions}")
        
        # Reset environment
        state, _ = env.reset()
        
        # Take the action
        next_state, reward, done, truncated, info = env.step(actions)
        
        print(f"Reward: {reward}")
        print(f"Cargo delivered: {sum(env.cargo_delivered.values())}")
        
        # Update Q-table for this state-action pair
        for j, action in enumerate(actions):
            state_tuple = tuple(state.tolist()) + (j, action)
            current_q = agent.q_table.get(state_tuple, 0)
            new_q = current_q + 0.2 * (reward - current_q)  # Learning rate = 0.2
            agent.q_table[state_tuple] = new_q
        
        print(f"Updated Q-table for work actions")
    
    # Test the fixed agent
    print(f"\nTesting fixed agent:")
    state, _ = env.reset()
    
    for day in range(5):
        actions = agent.select_action(state)
        
        # Ensure actions match number of trains
        if len(actions) > 8:
            actions = actions[:8]
        elif len(actions) < 8:
            actions = list(actions) + [0] * (8 - len(actions))
        
        print(f"Day {day + 1} actions: {actions}")
        
        next_state, reward, done, truncated, info = env.step(actions)
        cargo_delivered = sum(env.cargo_delivered.values())
        print(f"   Reward: {reward}, Cargo delivered: {cargo_delivered}")
        
        state = next_state
        
        if done:
            break
    
    final_cargo = sum(env.cargo_delivered.values())
    print(f"\nFINAL RESULT: {final_cargo} tons delivered")
    
    # Save the fixed agent
    agent.save('models/multi_route_agent_tazara_network_fixed.pkl')
    print(f"Fixed TAZARA agent saved to models/multi_route_agent_tazara_network_fixed.pkl")
    
    # Update API path
    print(f"\nUpdate API to use:")
    print(f"UNIVERSAL_MODEL_PATH = 'models/multi_route_agent_tazara_network_fixed.pkl'")

if __name__ == "__main__":
    fix_tazara_agent()
