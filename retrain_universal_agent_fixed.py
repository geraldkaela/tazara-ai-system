#!/usr/bin/env python3
"""
Retrain Universal Agent with Fixed Reward Function
Trains agent to deliver cargo instead of idling
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent

def train_universal_agent_fixed():
    """Train universal agent with corrected reward function"""
    
    print("RETRAINING UNIVERSAL AGENT WITH FIXED REWARDS")
    print("=" * 60)
    
    try:
        # Create training scenarios
        scenarios = [
            {"num_trains": 3, "cargo": {"DAR_KAPIRI": 500, "DAR_MBEYA": 500, "KAPIRI_NDOLA": 500}},
            {"num_trains": 5, "cargo": {"DAR_KAPIRI": 1000, "DAR_MBEYA": 1000, "KAPIRI_NDOLA": 1000}},
            {"num_trains": 8, "cargo": {"DAR_KAPIRI": 1500, "DAR_MBEYA": 1500, "KAPIRI_NDOLA": 1500}},
            {"num_trains": 12, "cargo": {"DAR_KAPIRI": 2000, "DAR_MBEYA": 2000, "KAPIRI_NDOLA": 2000}}
        ]
        
        print(f"Training {len(scenarios)} scenarios")
        
        # Train universal agent on all scenarios
        agent = MultiRouteAgent(
            state_bins=(10,) * 20,
            action_size=4
        )
        
        total_episodes = 0
        
        for scenario in scenarios:
            print(f"\nTraining scenario: {scenario['num_trains']} trains")
            
            # Create environment
            env = MultiRouteTazaraEnv(
                num_trains=scenario['num_trains'],
                max_cargo=5000,
                cargo_requirements=scenario['cargo']
            )
            
            # Train for multiple episodes
            episodes = 500
            for episode in range(episodes):
                state, _ = env.reset()
                
                for step in range(14):  # Max 14 days
                    actions = agent.select_action(state)
                    next_state, reward, done, truncated, info = env.step(actions)
                    agent.learn(state, actions, reward, next_state, done)
                    state = next_state
                    
                    if done:
                        break
                
                total_episodes += 1
            
            print(f"   - Episodes completed: {episodes}")
            
            total_episodes += episodes
        
        print(f"\nTotal training episodes: {total_episodes}")
        
        # Save universal agent
        agent.save('models/multi_route_agent_universal_fixed.pkl')
        print("Universal agent saved to models/multi_route_agent_universal_fixed.pkl")
        
        # Test the trained agent
        print(f"\nTesting trained agent...")
        
        # Test with 5 trains
        test_env = MultiRouteTazaraEnv(
            num_trains=5,
            max_cargo=5000,
            cargo_requirements={"DAR_KAPIRI": 1000, "DAR_MBEYA": 1000, "KAPIRI_NDOLA": 1000}
        )
        
        state, _ = test_env.reset()
        cargo_delivered_total = 0
        
        for step in range(14):
            actions = agent.select_action(state)
            next_state, reward, done, truncated, info = test_env.step(actions)
            cargo_delivered_total += sum(test_env.cargo_delivered.values())
            state = next_state
            
            if done:
                break
        
        print(f"Test results:")
        print(f"   - Total cargo delivered: {cargo_delivered_total}")
        print(f"   - Average per day: {cargo_delivered_total/14:.1f}")
        
        if cargo_delivered_total > 0:
            print("SUCCESS: Agent now delivers cargo!")
        else:
            print("ISSUE: Agent still not delivering cargo")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    train_universal_agent_fixed()
