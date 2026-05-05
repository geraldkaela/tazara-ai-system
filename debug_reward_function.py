#!/usr/bin/env python3
"""
Debug the reward function to understand why agent prefers idling
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent

def debug_rewards():
    """Debug reward calculation for different actions"""
    
    print("DEBUGGING REWARD FUNCTION")
    print("=" * 40)
    
    try:
        # Create environment
        env = MultiRouteTazaraEnv(
            num_trains=4,
            max_cargo=5000,
            cargo_requirements={"DAR_KAPIRI": 499, "DAR_MBEYA": 98, "KAPIRI_NDOLA": 500}
        )
        
        # Create agent with exploration disabled
        agent = MultiRouteAgent(
            state_bins=(10,) * 20,
            action_size=4
        )
        agent.exploration_rate = 0.0  # No exploration
        
        # Load the trained universal agent
        agent.load('models/multi_route_agent_universal_true.pkl')
        
        print(f"Initial cargo: {env.current_cargo}")
        print(f"Agent exploration rate: {agent.exploration_rate}")
        
        # Test different actions manually
        state, _ = env.reset()
        
        # Test action 0 (idle)
        print(f"\n--- Testing IDLE action (0) ---")
        actions_idle = [0, 0, 0, 0]
        next_state, reward_idle, done, truncated, info = env.step(actions_idle)
        print(f"Idle reward: {reward_idle}")
        print(f"Cargo after idle: {sum(env.cargo_delivered.values())}")
        
        # Reset for action test
        state, _ = env.reset()
        
        # Test action 1 (DAR_KAPIRI)
        print(f"\n--- Testing DAR_KAPIRI action (1) ---")
        actions_work = [1, 1, 1, 1]
        next_state, reward_work, done, truncated, info = env.step(actions_work)
        print(f"Work reward: {reward_work}")
        print(f"Cargo after work: {sum(env.cargo_delivered.values())}")
        
        # Reset for action test
        state, _ = env.reset()
        
        # Test action 2 (DAR_MBEYA)
        print(f"\n--- Testing DAR_MBEYA action (2) ---")
        actions_work2 = [2, 2, 2, 2]
        next_state, reward_work2, done, truncated, info = env.step(actions_work2)
        print(f"Work2 reward: {reward_work2}")
        print(f"Cargo after work2: {sum(env.cargo_delivered.values())}")
        
        # Reset for action test
        state, _ = env.reset()
        
        # Test action 3 (KAPIRI_NDOLA)
        print(f"\n--- Testing KAPIRI_NDOLA action (3) ---")
        actions_work3 = [3, 3, 3, 3]
        next_state, reward_work3, done, truncated, info = env.step(actions_work3)
        print(f"Work3 reward: {reward_work3}")
        print(f"Cargo after work3: {sum(env.cargo_delivered.values())}")
        
        print(f"\n--- REWARD COMPARISON ---")
        print(f"Idle (0): {reward_idle}")
        print(f"DAR_KAPIRI (1): {reward_work}")
        print(f"DAR_MBEYA (2): {reward_work2}")
        print(f"KAPIRI_NDOLA (3): {reward_work3}")
        
        # Test agent's actual choice
        state, _ = env.reset()
        agent_actions = agent.select_action(state)
        print(f"\n--- AGENT'S CHOICE ---")
        print(f"Agent actions: {agent_actions}")
        print(f"Agent prefers: {'IDLE' if all(a == 0 for a in agent_actions) else 'WORK'}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_rewards()
