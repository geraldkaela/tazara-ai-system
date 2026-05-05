#!/usr/bin/env python3
"""
Force agent to try work actions and learn the rewards
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent

def force_agent_work():
    """Force agent to try work actions and learn"""
    
    print("FORCING AGENT TO LEARN WORK ACTIONS")
    print("=" * 45)
    
    try:
        # Load the universal agent
        agent = MultiRouteAgent(
            state_bins=(10,) * 20,
            action_size=4
        )
        agent.load('models/multi_route_agent_universal_true.pkl')
        agent.exploration_rate = 0.0  # No exploration
        
        # Create environment
        env = MultiRouteTazaraEnv(
            num_trains=4,
            max_cargo=5000,
            cargo_requirements={"DAR_KAPIRI": 499, "DAR_MBEYA": 98, "KAPIRI_NDOLA": 500}
        )
        
        print(f"Initial cargo: {env.current_cargo}")
        
        # Force agent to try work actions and learn
        state, _ = env.reset()
        
        # Test different work actions
        work_actions = [
            [1, 1, 1, 1],  # All DAR_KAPIRI
            [2, 2, 2, 2],  # All DAR_MBEYA  
            [3, 3, 3, 3],  # All KAPIRI_NDOLA
            [1, 2, 3, 0],  # Mixed routes
            [1, 1, 2, 2],  # Two routes
        ]
        
        for i, actions in enumerate(work_actions):
            print(f"\n--- Testing work action set {i+1}: {actions} ---")
            
            # Reset environment
            state, _ = env.reset()
            
            # Take the action
            next_state, reward, done, truncated, info = env.step(actions)
            
            # Force the agent to learn this is good
            print(f"Reward: {reward}")
            print(f"Cargo delivered: {sum(env.cargo_delivered.values())}")
            
            # Update Q-table manually for this state-action pair
            for j, action in enumerate(actions):
                # This is a simplified Q-learning update
                current_q = agent.q_table.get(tuple(state.tolist()) + (j, action), 0)
                new_q = current_q + 0.1 * (reward - current_q)  # Learning rate = 0.1
                agent.q_table[tuple(state.tolist()) + (j, action)] = new_q
            
            print(f"Updated Q-table for work actions")
        
        # Test if agent now prefers work
        print(f"\n--- TESTING AGENT AFTER LEARNING ---")
        state, _ = env.reset()
        agent_actions = agent.select_action(state)
        print(f"Agent actions: {agent_actions}")
        print(f"Agent now prefers: {'IDLE' if all(a == 0 for a in agent_actions) else 'WORK'}")
        
        # Save the updated agent
        agent.save('models/multi_route_agent_universal_working.pkl')
        print("Updated agent saved to models/multi_route_agent_universal_working.pkl")
        
        # Test with a few days
        print(f"\n--- TESTING 5-DAY SIMULATION ---")
        state, _ = env.reset()
        total_cargo = 0
        
        for day in range(5):
            actions = agent.select_action(state)
            print(f"Day {day + 1} actions: {actions}")
            
            next_state, reward, done, truncated, info = env.step(actions)
            total_cargo += sum(env.cargo_delivered.values())
            
            print(f"   Reward: {reward}, Total cargo: {total_cargo}")
            
            state = next_state
            
            if done:
                break
        
        if total_cargo > 0:
            print(f"SUCCESS: Agent delivered {total_cargo} tons!")
        else:
            print("ISSUE: Agent still not delivering")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    force_agent_work()
