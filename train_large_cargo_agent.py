#!/usr/bin/env python3
"""
Train agent for large cargo scenarios (1000+ tons)
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent

def train_large_cargo_agent():
    """Train agent for large cargo scenarios"""
    
    print("TRAINING LARGE CARGO AGENT (1000+ TONS)")
    print("=" * 50)
    
    try:
        # Create agent
        agent = MultiRouteAgent(
            state_bins=(10,) * 20,
            action_size=4
        )
        agent.exploration_rate = 0.0  # No exploration
        
        # Large cargo scenarios
        scenarios = [
            {"num_trains": 7, "cargo": {"DAR_KAPIRI": 1000, "DAR_MBEYA": 1000, "KAPIRI_NDOLA": 500}},
            {"num_trains": 8, "cargo": {"DAR_KAPIRI": 1200, "DAR_MBEYA": 1200, "KAPIRI_NDOLA": 600}},
            {"num_trains": 10, "cargo": {"DAR_KAPIRI": 1500, "DAR_MBEYA": 1500, "KAPIRI_NDOLA": 800}},
        ]
        
        for scenario in scenarios:
            print(f"\nTraining: {scenario['num_trains']} trains, cargo: {scenario['cargo']}")
            
            # Create environment
            env = MultiRouteTazaraEnv(
                num_trains=scenario['num_trains'],
                max_cargo=5000,
                cargo_requirements=scenario['cargo']
            )
            
            # Train for 400 episodes
            for episode in range(400):
                state, _ = env.reset()
                total_reward = 0
                
                for step in range(14):  # 14 days
                    # Force work actions for first several steps to learn
                    if step < 6:
                        # Distribute trains across all routes with cargo
                        actions = []
                        trains_per_route = scenario['num_trains'] // 3
                        remaining = scenario['num_trains'] % 3
                        
                        # Assign trains to routes based on cargo volume
                        route_assignments = []
                        cargo_volumes = [(route, scenario['cargo'][route]) for route in env.route_names]
                        cargo_volumes.sort(key=lambda x: x[1], reverse=True)  # Sort by cargo amount
                        
                        for i, (route, cargo) in enumerate(cargo_volumes):
                            if cargo > 0:
                                trains_for_this_route = trains_per_route + (1 if i < remaining else 0)
                                route_assignments.extend([env.route_names.index(route) + 1] * trains_for_this_route)
                        
                        # Fill remaining with idle if needed
                        while len(route_assignments) < scenario['num_trains']:
                            route_assignments.append(0)
                        
                        actions = route_assignments[:scenario['num_trains']]
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
        print(f"\nTesting your scenario: 7 trains, cargo: DAR_KAPIRI=1000, DAR_MBEYA=1000, KAPIRI_NDOLA=500")
        
        test_env = MultiRouteTazaraEnv(
            num_trains=7,
            max_cargo=5000,
            cargo_requirements={"DAR_KAPIRI": 1000, "DAR_MBEYA": 1000, "KAPIRI_NDOLA": 500}
        )
        
        state, _ = test_env.reset()
        
        for day in range(7):
            actions = agent.select_action(state)
            print(f"Day {day + 1} actions: {actions}")
            
            next_state, reward, done, truncated, info = test_env.step(actions)
            print(f"   Reward: {reward}, Cargo delivered: {sum(test_env.cargo_delivered.values())}")
            
            state = next_state
            
            if done:
                break
        
        final_cargo = sum(test_env.cargo_delivered.values())
        if final_cargo > 0:
            print(f"SUCCESS: Agent delivered {final_cargo} tons!")
        else:
            print("ISSUE: Agent still not delivering")
        
        # Save the large cargo agent
        agent.save('models/multi_route_agent_large_cargo.pkl')
        print("Large cargo agent saved to models/multi_route_agent_large_cargo.pkl")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    train_large_cargo_agent()
