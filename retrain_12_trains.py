#!/usr/bin/env python3
"""
Retrain AI agent for 12 trains with maximum cargo capacity
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent

def retrain_12_trains():
    """Retrain AI agent for 12 trains with maximum cargo"""
    
    print("🚀 Retraining AI Agent for 12 Trains (MAXIMUM)...")
    print("=" * 60)
    
    # Maximum cargo amounts for 12 trains
    max_cargo = {
        "DAR_KAPIRI": 2000,  # Large capacity
        "DAR_MBEYA": 2000,   # Large capacity  
        "KAPIRI_NDOLA": 2000  # Large capacity
    }
    
    total_cargo = sum(max_cargo.values())
    
    # Create environment with 12 trains and maximum cargo
    env = MultiRouteTazaraEnv(
        num_trains=12,
        max_cargo=6000,
        cargo_requirements=max_cargo
    )
    
    print(f"📊 Environment Created:")
    print(f"  - Number of Trains: {env.total_trains}")
    print(f"  - Cargo Requirements: {env.cargo_requirements}")
    print(f"  - Total Cargo: {total_cargo} tons")
    print(f"  - Tons per Train: {total_cargo / env.total_trains:.1f}")
    print()
    
    # Create new agent (fresh Q-table)
    agent = MultiRouteAgent(
        state_bins=(10,) * 20,
        action_size=4,  # 3 routes + IDLE
        learning_rate=0.1,
        discount_factor=0.99,
        exploration_rate=1.0,
        exploration_decay=0.995,
        exploration_min=0.01
    )
    
    print("🤖 New Agent Created (Fresh Q-table)")
    print(f"  - Learning Rate: {agent.learning_rate}")
    print(f"  - Exploration Rate: {agent.exploration_rate}")
    print(f"  - Action Size: {agent.action_size}")
    print()
    
    # Training parameters - more episodes for 12 trains
    num_episodes = 200  # More episodes for complex 12-train operations
    max_steps_per_episode = 14  # 14 days
    
    print(f"🎯 Training Parameters:")
    print(f"  - Episodes: {num_episodes}")
    print(f"  - Max Steps per Episode: {max_steps_per_episode}")
    print()
    
    # Training loop
    print("🏋️ Starting Training...")
    print("-" * 60)
    
    best_reward = float('-inf')
    best_cargo = 0
    
    for episode in range(num_episodes):
        state, _ = env.reset()
        total_reward = 0
        steps = 0
        
        for step in range(max_steps_per_episode):
            # Choose action (explore-exploit)
            actions = agent.select_action(state)
            
            # Take action
            next_state, reward, done, truncated, info = env.step(actions)
            
            # Store experience and learn
            agent.learn(state, actions, reward, next_state, done or truncated)
            
            state = next_state
            total_reward += reward
            steps += 1
            
            if done or truncated:
                break
        
        # Track best performance
        cargo_delivered = sum(env.cargo_delivered.values())
        if total_reward > best_reward:
            best_reward = total_reward
        if cargo_delivered > best_cargo:
            best_cargo = cargo_delivered
        
        # Print progress
        if (episode + 1) % 20 == 0:
            print(f"Episode {episode + 1:3d}: Reward = {total_reward:10.1f}, Cargo = {cargo_delivered:4.0f} tons, Exploration = {agent.exploration_rate:.3f}")
    
    print("-" * 60)
    print("🎉 Training Complete!")
    print(f"🏆 Best Reward: ZMW {best_reward:,.0f}")
    print(f"🏆 Best Cargo: {best_cargo:.0f} tons")
    print()
    
    # Test the trained agent
    print("🧪 Testing Trained Agent...")
    print("-" * 60)
    
    state, _ = env.reset()
    total_reward = 0
    cargo_delivered = 0
    trains_working = 0
    
    for day in range(14):
        actions = agent.select_action(state)
        next_state, reward, done, truncated, info = env.step(actions)
        
        # Check if trains are working
        for action in actions:
            if action != 3:  # Not IDLE
                trains_working += 1
        
        # Get cargo delivered
        cargo_delivered = sum(env.cargo_delivered.values())
        
        print(f"Day {day + 1:2d}: Working = {sum(1 for a in actions if a != 3)}/{len(actions)}, Reward = {reward:10.1f}, Cargo = {cargo_delivered:4.0f} tons")
        
        state = next_state
        total_reward += reward
        
        if done or truncated:
            break
    
    print("-" * 60)
    print("📊 Test Results:")
    print(f"  - Total Reward: ZMW {total_reward:,.0f}")
    print(f"  - Cargo Delivered: {cargo_delivered:.0f} tons out of {total_cargo}")
    print(f"  - Delivery Rate: {(cargo_delivered/total_cargo)*100:.1f}%")
    print(f"  - Trains Working: {trains_working} out of {env.total_trains * 14} possible")
    print(f"  - Final Exploration Rate: {agent.exploration_rate:.3f}")
    print()
    
    # Save the trained agent
    model_path = "models/multi_route_agent_12_trains.pkl"
    try:
        agent.save(model_path)
        print(f"✅ Trained Agent Saved to: {model_path}")
    except Exception as e:
        print(f"❌ Failed to save agent: {e}")
    
    print()
    print("🎯 Training Summary:")
    efficiency = (cargo_delivered/total_cargo)*100
    if efficiency > 70:  # Expect to deliver at least 70% of maximum cargo
        print("✅ SUCCESS: Agent learned to handle 12 trains and maximum cargo!")
        print(f"   Delivered {cargo_delivered:.0f} tons ({efficiency:.1f}% efficiency)")
        print(f"   Generated ZMW {total_reward:,.0f} profit")
    elif efficiency > 50:
        print("⚠️  GOOD: Agent handling 12 trains reasonably well")
        print(f"   Delivered {cargo_delivered:.0f} tons ({efficiency:.1f}% efficiency)")
        print("   Could benefit from more training")
    else:
        print("❌ ISSUE: Agent struggling with 12 trains")
        print("   May need more training episodes or different approach")
    
    return agent

if __name__ == "__main__":
    retrain_12_trains()
