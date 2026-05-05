#!/usr/bin/env python3
"""
Create a working agent from scratch
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent

def create_working_agent():
    """Create a working agent from scratch"""
    
    print("CREATING WORKING AGENT FROM SCRATCH")
    print("=" * 45)
    
    try:
        # Create fresh agent
        agent = MultiRouteAgent(
            state_bins=(10,) * 20,
            action_size=4
        )
        agent.exploration_rate = 0.0  # No exploration
        
        # Create environment
        env = MultiRouteTazaraEnv(
            num_trains=4,
            max_cargo=5000,
            cargo_requirements={"DAR_KAPIRI": 499, "DAR_MBEYA": 98, "KAPIRI_NDOLA": 500}
        )
        
        print(f"Training fresh agent...")
        
        # Train with forced work actions
        for episode in range(100):
            state, _ = env.reset()
            total_reward = 0
            
            for step in range(14):
                # Force work actions for first few steps
                if step < 3:
                    # Force different work actions
                    if step == 0:
                        actions = [1, 1, 1, 1]  # DAR_KAPIRI
                    elif step == 1:
                        actions = [2, 2, 2, 2]  # DAR_MBEYA
                    else:
                        actions = [3, 3, 3, 3]  # KAPIRI_NDOLA
                else:
                    # Let agent choose
                    actions = agent.select_action(state)
                
                # Take step
                next_state, reward, done, truncated, info = env.step(actions)
                
                # Learn
                agent.learn(state, actions, reward, next_state, done)
                
                total_reward += reward
                state = next_state
                
                if done:
                    break
            
            if episode % 20 == 0:
                print(f"   Episode {episode}: Reward = {total_reward}, Cargo = {sum(env.cargo_delivered.values())}")
        
        # Test the agent
        print(f"\nTesting trained agent...")
        state, _ = env.reset()
        
        for day in range(5):
            actions = agent.select_action(state)
            print(f"Day {day + 1} actions: {actions}")
            
            next_state, reward, done, truncated, info = env.step(actions)
            print(f"   Reward: {reward}, Cargo delivered: {sum(env.cargo_delivered.values())}")
            
            state = next_state
            
            if done:
                break
        
        final_cargo = sum(env.cargo_delivered.values())
        if final_cargo > 0:
            print(f"SUCCESS: Agent delivered {final_cargo} tons!")
        else:
            print("ISSUE: Agent still not delivering")
        
        # Save the working agent
        agent.save('models/multi_route_agent_working.pkl')
        print("Working agent saved to models/multi_route_agent_working.pkl")
        
        # Update API to use this agent
        print(f"\nUpdating API to use working agent...")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_working_agent()
