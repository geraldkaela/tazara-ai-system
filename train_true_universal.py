#!/usr/bin/env python3
"""
Train True Universal Agent for 1-12 trains
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent

def train_true_universal():
    """Train universal agent that can handle any train count"""
    
    print("TRAINING TRUE UNIVERSAL AGENT (1-12 TRAINS)")
    print("=" * 60)
    
    try:
        # Create agent with larger state space for variable train counts
        agent = MultiRouteAgent(
            state_bins=(10,) * 20,
            action_size=4
        )
        
        # Train on multiple train counts
        train_scenarios = [
            {"num_trains": 3, "cargo": {"DAR_KAPIRI": 500, "DAR_MBEYA": 300, "KAPIRI_NDOLA": 400}},
            {"num_trains": 4, "cargo": {"DAR_KAPIRI": 600, "DAR_MBEYA": 400, "KAPIRI_NDOLA": 500}},
            {"num_trains": 5, "cargo": {"DAR_KAPIRI": 800, "DAR_MBEYA": 500, "KAPIRI_NDOLA": 600}},
            {"num_trains": 6, "cargo": {"DAR_KAPIRI": 1000, "DAR_MBEYA": 600, "KAPIRI_NDOLA": 700}},
            {"num_trains": 8, "cargo": {"DAR_KAPIRI": 1200, "DAR_MBEYA": 800, "KAPIRI_NDOLA": 900}},
            {"num_trains": 10, "cargo": {"DAR_KAPIRI": 1500, "DAR_MBEYA": 1000, "KAPIRI_NDOLA": 1200}},
            {"num_trains": 12, "cargo": {"DAR_KAPIRI": 1800, "DAR_MBEYA": 1200, "KAPIRI_NDOLA": 1500}}
        ]
        
        total_episodes = 0
        
        for scenario in train_scenarios:
            print(f"\nTraining with {scenario['num_trains']} trains...")
            
            # Create environment
            env = MultiRouteTazaraEnv(
                num_trains=scenario['num_trains'],
                max_cargo=5000,
                cargo_requirements=scenario['cargo']
            )
            
            # Train for multiple episodes
            episodes = 300
            for episode in range(episodes):
                state, _ = env.reset()
                total_reward = 0
                
                for step in range(14):  # 14 days
                    # Get actions
                    actions = agent.select_action(state)
                    
                    # Take step
                    next_state, reward, done, truncated, info = env.step(actions)
                    
                    # Learn
                    agent.learn(state, actions, reward, next_state, done)
                    
                    total_reward += reward
                    state = next_state
                    
                    if done:
                        break
                
                total_episodes += 1
                
                if episode % 100 == 0:
                    print(f"   Episode {episode}: Reward = {total_reward}, Cargo = {sum(env.cargo_delivered.values())}")
            
            # Test after training this scenario
            print(f"   Testing {scenario['num_trains']} trains...")
            state, _ = env.reset()
            cargo_delivered = 0
            
            for step in range(14):
                actions = agent.select_action(state)
                next_state, reward, done, truncated, info = env.step(actions)
                cargo_delivered += sum(env.cargo_delivered.values())
                state = next_state
                
                if done:
                    break
            
            print(f"   Result: {cargo_delivered} tons delivered")
        
        print(f"\nTotal training episodes: {total_episodes}")
        
        # Save universal agent
        agent.save('models/multi_route_agent_universal_true.pkl')
        print("Universal agent saved to models/multi_route_agent_universal_true.pkl")
        
        # Test with 4 trains (your current use case)
        print(f"\nTesting with 4 trains...")
        test_env = MultiRouteTazaraEnv(
            num_trains=4,
            max_cargo=5000,
            cargo_requirements={"DAR_KAPIRI": 499, "DAR_MBEYA": 98, "KAPIRI_NDOLA": 500}
        )
        
        state, _ = test_env.reset()
        
        for step in range(5):
            actions = agent.select_action(state)
            print(f"   Day {step + 1} actions: {actions}")
            
            next_state, reward, done, truncated, info = test_env.step(actions)
            print(f"   Reward: {reward}, Cargo delivered: {sum(test_env.cargo_delivered.values())}")
            
            state = next_state
            
            if done:
                break
        
        final_cargo = sum(test_env.cargo_delivered.values())
        if final_cargo > 0:
            print(f"SUCCESS: Agent delivered {final_cargo} tons with 4 trains!")
        else:
            print("ISSUE: Agent still not delivering cargo with 4 trains")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    train_true_universal()
