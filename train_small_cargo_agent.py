#!/usr/bin/env python3
"""
Train agent for small cargo scenarios (1-10 tons)
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent

def train_small_cargo_agent():
    """Train agent for small cargo scenarios"""
    
    print("TRAINING SMALL CARGO AGENT")
    print("=" * 40)
    
    try:
        # Create agent
        agent = MultiRouteAgent(
            state_bins=(10,) * 20,
            action_size=4
        )
        agent.exploration_rate = 0.0  # No exploration
        
        # Small cargo scenarios
        scenarios = [
            {"num_trains": 1, "cargo": {"DAR_KAPIRI": 0, "DAR_MBEYA": 1, "KAPIRI_NDOLA": 1}},
            {"num_trains": 1, "cargo": {"DAR_KAPIRI": 2, "DAR_MBEYA": 2, "KAPIRI_NDOLA": 2}},
            {"num_trains": 2, "cargo": {"DAR_KAPIRI": 1, "DAR_MBEYA": 1, "KAPIRI_NDOLA": 1}},
            {"num_trains": 3, "cargo": {"DAR_KAPIRI": 2, "DAR_MBEYA": 2, "KAPIRI_NDOLA": 2}},
            {"num_trains": 4, "cargo": {"DAR_KAPIRI": 0, "DAR_MBEYA": 1, "KAPIRI_NDOLA": 1}},
        ]
        
        for scenario in scenarios:
            print(f"\nTraining: {scenario['num_trains']} trains, cargo: {scenario['cargo']}")
            
            # Create environment
            env = MultiRouteTazaraEnv(
                num_trains=scenario['num_trains'],
                max_cargo=5000,
                cargo_requirements=scenario['cargo']
            )
            
            # Train for 200 episodes
            for episode in range(200):
                state, _ = env.reset()
                total_reward = 0
                
                for step in range(7):  # Shorter horizon for small cargo
                    # Force work actions for first few steps to learn
                    if step < 2:
                        # Choose routes that actually have cargo
                        available_routes = [i for i, route in enumerate(env.route_names) 
                                          if env.current_cargo[route] > 0]
                        if available_routes:
                            # Assign all trains to first available route
                            route_idx = available_routes[0]
                            actions = [route_idx + 1] * scenario['num_trains']  # +1 because action 0 = idle
                        else:
                            actions = [0] * scenario['num_trains']  # All idle if no cargo
                    else:
                        actions = agent.select_action(state)
                    
                    # Take step
                    next_state, reward, done, truncated, info = env.step(actions)
                    
                    # Learn
                    agent.learn(state, actions, reward, next_state, done)
                    
                    total_reward += reward
                    state = next_state
                    
                    if done:
                        break
                
                if episode % 50 == 0:
                    print(f"   Episode {episode}: Reward = {total_reward}, Cargo = {sum(env.cargo_delivered.values())}")
        
        # Test on your specific scenario
        print(f"\nTesting your scenario: 1 train, cargo: DAR_KAPIRI=0, DAR_MBEYA=1, KAPIRI_NDOLA=1")
        
        test_env = MultiRouteTazaraEnv(
            num_trains=1,
            max_cargo=5000,
            cargo_requirements={"DAR_KAPIRI": 0, "DAR_MBEYA": 1, "KAPIRI_NDOLA": 1}
        )
        
        state, _ = test_env.reset()
        
        for day in range(5):
            actions = agent.select_action(state)
            print(f"Day {day + 1} actions: {actions}")
            
            next_state, reward, done, truncated, info = test_env.step(actions)
            print(f"   Reward: {reward}, Cargo delivered: {sum(test_env.cargo_delivered.values())}")
            print(f"   Current cargo: {test_env.current_cargo}")
            
            state = next_state
            
            if done:
                break
        
        final_cargo = sum(test_env.cargo_delivered.values())
        if final_cargo > 0:
            print(f"SUCCESS: Agent delivered {final_cargo} tons!")
        else:
            print("ISSUE: Agent still not delivering")
        
        # Save the small cargo agent
        agent.save('models/multi_route_agent_small_cargo.pkl')
        print("Small cargo agent saved to models/multi_route_agent_small_cargo.pkl")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    train_small_cargo_agent()
