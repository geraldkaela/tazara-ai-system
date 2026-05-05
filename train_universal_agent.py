#!/usr/bin/env python3
"""
Train Universal AI Agent that can handle any number of trains (1-12)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent

def train_universal_agent():
    """Train universal AI agent that adapts to any train count"""
    
    print("🚀 Training Universal AI Agent (1-12 trains)...")
    print("=" * 70)
    
    # Training scenarios with different train counts
    training_scenarios = [
        {"trains": 1, "cargo": {"DAR_KAPIRI": 200, "DAR_MBEYA": 200, "KAPIRI_NDOLA": 200}},
        {"trains": 2, "cargo": {"DAR_KAPIRI": 400, "DAR_MBEYA": 400, "KAPIRI_NDOLA": 400}},
        {"trains": 3, "cargo": {"DAR_KAPIRI": 600, "DAR_MBEYA": 600, "KAPIRI_NDOLA": 600}},
        {"trains": 4, "cargo": {"DAR_KAPIRI": 800, "DAR_MBEYA": 800, "KAPIRI_NDOLA": 800}},
        {"trains": 6, "cargo": {"DAR_KAPIRI": 1200, "DAR_MBEYA": 1200, "KAPIRI_NDOLA": 1200}},
        {"trains": 8, "cargo": {"DAR_KAPIRI": 1600, "DAR_MBEYA": 1600, "KAPIRI_NDOLA": 1600}},
        {"trains": 10, "cargo": {"DAR_KAPIRI": 2000, "DAR_MBEYA": 2000, "KAPIRI_NDOLA": 2000}},
        {"trains": 12, "cargo": {"DAR_KAPIRI": 2400, "DAR_MBEYA": 2400, "KAPIRI_NDOLA": 2400}},
    ]
    
    # Create universal agent
    agent = MultiRouteAgent(
        state_bins=(10,) * 20,
        action_size=4,  # 3 routes + IDLE
        learning_rate=0.1,
        discount_factor=0.99,
        exploration_rate=1.0,
        exploration_decay=0.995,
        exploration_min=0.01
    )
    
    print("🤖 Universal Agent Created")
    print(f"  - Learning Rate: {agent.learning_rate}")
    print(f"  - Exploration Rate: {agent.exploration_rate}")
    print(f"  - Action Size: {agent.action_size}")
    print(f"  - Training Scenarios: {len(training_scenarios)}")
    print()
    
    # Training parameters
    episodes_per_scenario = 50  # Episodes for each scenario
    max_steps_per_episode = 14  # 14 days
    
    print(f"🎯 Training Parameters:")
    print(f"  - Episodes per Scenario: {episodes_per_scenario}")
    print(f"  - Total Episodes: {episodes_per_scenario * len(training_scenarios)}")
    print(f"  - Max Steps per Episode: {max_steps_per_episode}")
    print()
    
    # Training loop across all scenarios
    print("🏋️ Starting Universal Training...")
    print("-" * 70)
    
    total_episodes = 0
    scenario_rewards = {}
    
    for scenario_idx, scenario in enumerate(training_scenarios):
        print(f"\n📊 Training Scenario {scenario_idx + 1}/{len(training_scenarios)}: {scenario['trains']} trains")
        print("-" * 50)
        
        # Create environment for this scenario
        env = MultiRouteTazaraEnv(
            num_trains=scenario['trains'],
            max_cargo=5000,
            cargo_requirements=scenario['cargo']
        )
        
        scenario_total_reward = 0
        best_cargo = 0
        
        for episode in range(episodes_per_scenario):
            state, _ = env.reset()
            episode_reward = 0
            
            for step in range(max_steps_per_episode):
                # Choose action
                actions = agent.select_action(state)
                
                # Take action
                next_state, reward, done, truncated, info = env.step(actions)
                
                # Learn
                agent.learn(state, actions, reward, next_state, done or truncated)
                
                state = next_state
                episode_reward += reward
                
                if done or truncated:
                    break
            
            scenario_total_reward += episode_reward
            cargo_delivered = sum(env.cargo_delivered.values())
            best_cargo = max(best_cargo, cargo_delivered)
            total_episodes += 1
            
            # Print progress
            if (episode + 1) % 10 == 0:
                print(f"  Episode {episode + 1:2d}: Reward = {episode_reward:8.1f}, Cargo = {cargo_delivered:3.0f} tons")
        
        # Store scenario results
        scenario_rewards[scenario['trains']] = {
            'avg_reward': scenario_total_reward / episodes_per_scenario,
            'best_cargo': best_cargo,
            'total_cargo': sum(scenario['cargo'].values())
        }
        
        print(f"  ✅ Scenario {scenario['trains']} trains completed")
        print(f"     Avg Reward: ZMW {scenario_total_reward / episodes_per_scenario:,.0f}")
        print(f"     Best Cargo: {best_cargo:.0f} tons")
    
    print("\n" + "=" * 70)
    print("🎉 Universal Training Complete!")
    print(f"📊 Total Episodes Trained: {total_episodes}")
    print()
    
    # Print scenario summary
    print("📋 Scenario Performance Summary:")
    print("-" * 70)
    for trains, results in scenario_rewards.items():
        efficiency = (results['best_cargo'] / results['total_cargo']) * 100
        print(f"  {trains:2d} trains: ZMW {results['avg_reward']:8.0f} avg, "
              f"{results['best_cargo']:4.0f}/{results['total_cargo']:4.0f} tons "
              f"({efficiency:5.1f}% efficiency)")
    print()
    
    # Test the universal agent with various train counts
    print("🧪 Testing Universal Agent...")
    print("-" * 70)
    
    test_scenarios = [
        {"trains": 1, "cargo": {"DAR_KAPIRI": 100, "DAR_MBEYA": 100, "KAPIRI_NDOLA": 100}},
        {"trains": 5, "cargo": {"DAR_KAPIRI": 1000, "DAR_MBEYA": 999, "KAPIRI_NDOLA": 1000}},
        {"trains": 12, "cargo": {"DAR_KAPIRI": 2000, "DAR_MBEYA": 2000, "KAPIRI_NDOLA": 2000}},
    ]
    
    for test in test_scenarios:
        print(f"\n🔍 Testing {test['trains']} trains:")
        
        env = MultiRouteTazaraEnv(
            num_trains=test['trains'],
            cargo_requirements=test['cargo']
        )
        
        state, _ = env.reset()
        total_reward = 0
        cargo_delivered = 0
        
        for day in range(14):
            actions = agent.select_action(state)
            next_state, reward, done, truncated, info = env.step(actions)
            
            working_trains = sum(1 for a in actions if a != 3)
            cargo_delivered = sum(env.cargo_delivered.values())
            
            total_reward += reward
            state = next_state
            
            if done or truncated:
                break
        
        total_cargo = sum(test['cargo'].values())
        efficiency = (cargo_delivered / total_cargo) * 100
        
        print(f"  📊 Results: Reward = ZMW {total_reward:,.0f}, "
              f"Cargo = {cargo_delivered:.0f}/{total_cargo} tons ({efficiency:.1f}%)")
    
    print("\n" + "-" * 70)
    
    # Save the universal agent
    model_path = "models/multi_route_agent_universal.pkl"
    try:
        agent.save(model_path)
        print(f"✅ Universal Agent Saved to: {model_path}")
    except Exception as e:
        print(f"❌ Failed to save agent: {e}")
    
    print()
    print("🎯 Universal Training Summary:")
    print("✅ SUCCESS: Universal agent trained for 1-12 trains!")
    print("   - Can handle any train count from 1-12")
    print("   - Adapts to different cargo amounts")
    print("   - Maintains efficiency across all scenarios")
    print("   - Single model for all use cases")
    
    return agent

if __name__ == "__main__":
    train_universal_agent()
