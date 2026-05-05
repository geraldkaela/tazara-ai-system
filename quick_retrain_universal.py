#!/usr/bin/env python3
"""
Quick retrain of universal agent with current reward function
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent

def quick_retrain():
    """Quick retrain with current reward function"""
    
    print("QUICK RETRAINING UNIVERSAL AGENT")
    print("=" * 50)
    
    try:
        # Create agent
        agent = MultiRouteAgent(
            state_bins=(10,) * 20,
            action_size=4
        )
        
        # Create environment with cargo
        env = MultiRouteTazaraEnv(
            num_trains=5,
            max_cargo=5000,
            cargo_requirements={
                "DAR_KAPIRI": 1000,
                "DAR_MBEYA": 1000,
                "KAPIRI_NDOLA": 500
            }
        )
        
        print(f"Training with current reward function...")
        
        # Train for 1000 episodes
        for episode in range(1000):
            state, _ = env.reset()
            total_reward = 0
            
            for step in range(14):  # 14 days
                # Get action
                actions = agent.select_action(state)
                
                # Take step
                next_state, reward, done, truncated, info = env.step(actions)
                
                # Learn
                agent.learn(state, actions, reward, next_state, done)
                
                total_reward += reward
                state = next_state
                
                if done:
                    break
            
            if episode % 100 == 0:
                print(f"   Episode {episode}: Total reward = {total_reward}")
        
        # Save agent
        agent.save('models/multi_route_agent_universal_v2.pkl')
        print("Agent saved to models/multi_route_agent_universal_v2.pkl")
        
        # Test the agent
        print(f"\nTesting agent...")
        state, _ = env.reset()
        
        for step in range(5):
            actions = agent.select_action(state)
            print(f"   Day {step + 1} actions: {actions}")
            
            next_state, reward, done, truncated, info = env.step(actions)
            print(f"   Reward: {reward}, Cargo delivered: {sum(env.cargo_delivered.values())}")
            
            state = next_state
            
            if done:
                break
        
        if sum(env.cargo_delivered.values()) > 0:
            print("SUCCESS: Agent now delivers cargo!")
        else:
            print("Agent still not delivering cargo")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_retrain()
