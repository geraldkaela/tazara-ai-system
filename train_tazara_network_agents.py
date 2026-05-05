#!/usr/bin/env python3
"""
Train AI agents for the complete TAZARA route network
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent

def train_tazara_network_agents():
    """Train agents for the complete TAZARA network"""
    
    print("TRAINING AI AGENTS FOR COMPLETE TAZARA NETWORK")
    print("=" * 60)
    
    # Training scenarios for different route types
    scenarios = [
        {
            "name": "Through Traffic Main Line",
            "num_trains": 8,
            "cargo": {
                "DAR_KAPIRI": 1000,
                "DAR_MBEYA": 800,
                "MBEYA_KASAMA": 600
            }
        },
        {
            "name": "Tanzania Local Routes",
            "num_trains": 6,
            "cargo": {
                "DAR_KIDATU": 400,
                "KIDATU_MAKAMBAKO": 300,
                "MAKAMBAKO_MBEYA": 350
            }
        },
        {
            "name": "Zambia Local Routes",
            "num_trains": 6,
            "cargo": {
                "KASAMA_MPIKA": 300,
                "MPIKA_SERENJE": 250,
                "SERENJE_KAPIRI": 200
            }
        },
        {
            "name": "Mixed Network Operations",
            "num_trains": 10,
            "cargo": {
                "DAR_KAPIRI": 800,
                "DAR_MBEYA": 600,
                "KAPIRI_NDOLA": 400,
                "DAR_KIDATU": 300,
                "KIDATU_TRANS_SHIPMENT": 200
            }
        },
        {
            "name": "Full Network Integration",
            "num_trains": 12,
            "cargo": {
                "DAR_KAPIRI": 1200,
                "DAR_MBEYA": 900,
                "MBEYA_KASAMA": 700,
                "KAPIRI_NDOLA": 500,
                "DAR_KIDATU": 400,
                "KIDATU_MAKAMBAKO": 300,
                "MAKAMBAKO_MBEYA": 350,
                "KASAMA_MPIKA": 250,
                "MPIKA_SERENJE": 200,
                "SERENJE_KAPIRI": 150,
                "KIDATU_TRANS_SHIPMENT": 100,
                "KAPIRI_DISTRIBUTION": 300
            }
        }
    ]
    
    # Create agent for 12-route system
    agent = MultiRouteAgent(
        state_bins=(10,) * 30,  # Larger state space for more routes
        action_size=13  # 12 routes + 1 idle
    )
    agent.exploration_rate = 0.1  # Start with exploration
    
    print(f"Agent created for 12 routes + idle = 13 actions")
    print(f"State space: 30 dimensions")
    
    # Train across all scenarios
    for scenario in scenarios:
        print(f"\n{'='*20}")
        print(f"TRAINING: {scenario['name']}")
        print(f"Trains: {scenario['num_trains']}")
        print(f"Cargo routes: {len([k for k, v in scenario['cargo'].items() if v > 0])}")
        print(f"{'='*20}")
        
        # Create environment
        env = MultiRouteTazaraEnv(
            num_trains=scenario['num_trains'],
            max_cargo=5000,
            cargo_requirements=scenario['cargo']
        )
        
        # Train for this scenario
        for episode in range(200):
            state, _ = env.reset()
            total_reward = 0
            
            for step in range(14):  # 14 days
                # Choose action - ensure action array matches number of trains
                actions = agent.select_action(state)
                
                # Trim or pad actions to match number of trains
                if len(actions) > scenario['num_trains']:
                    actions = actions[:scenario['num_trains']]
                elif len(actions) < scenario['num_trains']:
                    actions = list(actions) + [0] * (scenario['num_trains'] - len(actions))
                
                # Take step
                next_state, reward, done, truncated, info = env.step(actions)
                
                # Learn
                agent.learn(state, actions, reward, next_state, done)
                
                total_reward += reward
                state = next_state
                
                if done:
                    break
            
            if episode % 50 == 0:
                cargo_delivered = sum(env.cargo_delivered.values())
                print(f"   Episode {episode}: Reward = {total_reward:.0f}, Cargo = {cargo_delivered}")
        
        # Decrease exploration
        agent.exploration_rate = max(0.01, agent.exploration_rate * 0.9)
    
    # Final test
    print(f"\n{'='*20}")
    print("FINAL TESTING")
    print(f"{'='*20}")
    
    agent.exploration_rate = 0.0  # No exploration for testing
    
    # Test with full network
    test_env = MultiRouteTazaraEnv(
        num_trains=12,
        max_cargo=5000,
        cargo_requirements=scenarios[4]["cargo"]
    )
    
    state, _ = test_env.reset()
    
    for day in range(7):
        actions = agent.select_action(state)
        
        # Ensure actions match number of trains
        if len(actions) > 12:
            actions = actions[:12]
        elif len(actions) < 12:
            actions = list(actions) + [0] * (12 - len(actions))
        
        print(f"Day {day + 1} actions: {actions}")
        
        next_state, reward, done, truncated, info = test_env.step(actions)
        cargo_delivered = sum(test_env.cargo_delivered.values())
        print(f"   Reward: {reward:.0f}, Cargo delivered: {cargo_delivered}")
        
        state = next_state
        
        if done:
            break
    
    final_cargo = sum(test_env.cargo_delivered.values())
    print(f"\nFINAL RESULT: {final_cargo} tons delivered")
    
    # Save the trained agent
    agent.save('models/multi_route_agent_tazara_network.pkl')
    print(f"\nTAZARA Network Agent saved to models/multi_route_agent_tazara_network.pkl")
    
    # Update API to use new agent
    print(f"\nTo use the new agent, update the API to use:")
    print(f"UNIVERSAL_MODEL_PATH = 'models/multi_route_agent_tazara_network.pkl'")

if __name__ == "__main__":
    train_tazara_network_agents()
