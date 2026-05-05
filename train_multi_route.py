"""
Multi-Route TAZARA RL Training Script
Phase 2 - Multi-route scheduling implementation
"""

import os
import numpy as np
from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv
from reinforcement_rl.multi_route_agent import train_multi_route_agent, MultiRouteAgent
from reinforcement_rl.improved_cost_model import get_improved_cost_breakdown


def main():
    """Train multi-route RL agent"""
    
    print("🚂 TAZARA Multi-Route RL Training")
    print("=" * 50)
    
    # Create environment
    print("🌍 Initializing Multi-Route Environment...")
    env = MultiRouteTazaraEnv(
        num_trains=6,  # 6 trains operating simultaneously
        max_cargo=5000
    )
    
    print(f"📊 Environment Configuration:")
    print(f"   - Total Trains: {env.total_trains}")
    print(f"   - Routes: {env.route_names}")
    print(f"   - State Space: {env.observation_space}")
    print(f"   - Action Space: {env.action_space}")
    
    # Train agent
    print("\n🎯 Starting Training...")
    agent = train_multi_route_agent(
        env=env,
        episodes=500,  # Start with 500 episodes for testing
        max_steps_per_episode=50,
        save_path="models/multi_route_agent.pkl"
    )
    
    # Test trained agent
    print("\n🧪 Testing Trained Agent...")
    test_agent(env, agent)
    
    print("\n✅ Multi-Route Training Complete!")


def test_agent(env: MultiRouteTazaraEnv, agent: MultiRouteAgent):
    """Test the trained multi-route agent"""
    
    # Set exploration to 0 for evaluation
    original_exploration = agent.exploration_rate
    agent.exploration_rate = 0
    
    state, _ = env.reset()
    total_reward = 0
    steps = 0
    
    print("\n📈 Test Episode Results:")
    print("-" * 30)
    
    while True:
        # Get actions for all trains
        actions = agent.select_action(state)
        
        # Execute step
        next_state, reward, done, truncated, info = env.step(actions)
        
        total_reward += reward
        steps += 1
        
        # Display progress
        if steps % 5 == 0:
            print(f"Day {steps}: Reward={reward:.2f}, Total={total_reward:.2f}")
            env.render()
        
        state = next_state
        
        if done or truncated or steps >= 20:
            break
    
    # Get final metrics
    metrics = env.get_performance_metrics()
    cost_breakdown = get_improved_cost_breakdown(
        cargo_delivered=metrics['total_cargo_delivered'],
        trains_used=metrics['trains_used'],
        delay_days=metrics['delay_days'],
        idle_days=metrics['idle_days'],
        active_trains=metrics['active_trains']
    )
    
    print(f"\n📊 Final Performance Metrics:")
    print(f"   - Total Reward: {total_reward:.2f}")
    print(f"   - Cargo Delivered: {metrics['total_cargo_delivered']:.0f} tons")
    print(f"   - Trains Used: {metrics['trains_used']}")
    print(f"   - Active Trains: {metrics['active_trains']}")
    print(f"   - Delay Days: {metrics['delay_days']}")
    print(f"   - Idle Days: {metrics['idle_days']}")
    print(f"   - Efficiency: {metrics['efficiency']:.2f} tons/train")
    
    print(f"\n💰 ZMW Cost Breakdown:")
    print(f"   - Revenue: ZMW {cost_breakdown['revenue_zmw']:,.2f}")
    print(f"   - Train Cost: ZMW {cost_breakdown['train_cost_zmw']:,.2f}")
    print(f"   - Delay Cost: ZMW {cost_breakdown['delay_cost_zmw']:,.2f}")
    print(f"   - Idle Cost: ZMW {cost_breakdown['idle_cost_zmw']:,.2f}")
    print(f"   - Coordination Bonus: ZMW {cost_breakdown.get('coordination_bonus_zmw', 0):,.2f}")
    print(f"   - Net Profit: ZMW {cost_breakdown['net_profit_zmw']:,.2f}")
    print(f"   - Efficiency Score: {cost_breakdown.get('efficiency_score', 0):.1f}%")
    
    # Restore exploration rate
    agent.exploration_rate = original_exploration


if __name__ == "__main__":
    # Create models directory if it doesn't exist
    os.makedirs("models", exist_ok=True)
    
    main()
