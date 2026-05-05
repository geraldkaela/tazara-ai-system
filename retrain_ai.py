#!/usr/bin/env python3
"""
Retrain AI agent with new profitable economics
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import MultiRouteAgent
from reinforcement_rl.improved_cost_model import (
    dispatch_reward,
    train_usage_penalty,
    idle_penalty,
    get_improved_cost_breakdown
)

def retrain_ai_agent():
    """Retrain AI agent with new profitable economics"""
    
    print("🚀 Retraining AI Agent with New Economics...")
    print("=" * 60)
    
    # Create environment with user cargo requirements
    env = MultiRouteTazaraEnv(
        num_trains=3,
        max_cargo=5000,
        cargo_requirements={
            "DAR_KAPIRI": 100,
            "DAR_MBEYA": 100,
            "KAPIRI_NDOLA": 100
        }
    )
    
    print(f"📊 Environment Created:")
    print(f"  - Number of Trains: {env.total_trains}")
    print(f"  - Cargo Requirements: {env.cargo_requirements}")
    print(f"  - Available Routes: {env.route_names}")
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
    
    # Training parameters
    num_episodes = 100
    max_steps_per_episode = 14  # 14 days
    
    print(f"🎯 Training Parameters:")
    print(f"  - Episodes: {num_episodes}")
    print(f"  - Max Steps per Episode: {max_steps_per_episode}")
    print()
    
    # Training loop
    print("🏋️ Starting Training...")
    print("-" * 60)
    
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
        
        # Print progress
        if (episode + 1) % 10 == 0:
            print(f"Episode {episode + 1:3d}: Reward = {total_reward:8.1f}, Steps = {steps:2d}, Exploration = {agent.exploration_rate:.3f}")
    
    print("-" * 60)
    print("🎉 Training Complete!")
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
        
        print(f"Day {day + 1:2d}: Actions = {actions}, Reward = {reward:8.1f}, Cargo = {cargo_delivered:3.0f} tons")
        
        state = next_state
        total_reward += reward
        
        if done or truncated:
            break
    
    print("-" * 60)
    print("📊 Test Results:")
    print(f"  - Total Reward: ZMW {total_reward:,.0f}")
    print(f"  - Cargo Delivered: {cargo_delivered:.0f} tons")
    print(f"  - Trains Working: {trains_working} out of {env.total_trains * 14} possible")
    print(f"  - Final Exploration Rate: {agent.exploration_rate:.3f}")
    print()
    
    # Save the trained agent
    model_path = "models/multi_route_agent.pkl"
    try:
        agent.save(model_path)
        print(f"✅ Trained Agent Saved to: {model_path}")
    except Exception as e:
        print(f"❌ Failed to save agent: {e}")
    
    print()
    print("🎯 Training Summary:")
    if cargo_delivered > 0:
        print("✅ SUCCESS: Agent learned to work and deliver cargo!")
        print(f"   Delivered {cargo_delivered:.0f} tons with positive economics")
    else:
        print("❌ ISSUE: Agent still choosing IDLE")
        print("   May need more training episodes or different approach")
    
    return agent

if __name__ == "__main__":
    retrain_ai_agent()
