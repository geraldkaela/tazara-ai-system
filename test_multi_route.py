"""
Test Multi-Route Environment
Phase 2 - Multi-route scheduling
"""

import numpy as np
from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv


def test_environment():
    """Test the multi-route environment functionality"""
    
    print("🚂 Testing Multi-Route TAZARA Environment")
    print("=" * 50)
    
    # Create environment
    env = MultiRouteTazaraEnv(
        num_trains=4,  # Start with 4 trains for testing
        max_cargo=2000
    )
    
    print(f"📊 Environment Configuration:")
    print(f"   - Total Trains: {env.total_trains}")
    print(f"   - Routes: {env.route_names}")
    print(f"   - State Space Shape: {env.observation_space.shape}")
    print(f"   - Action Space Shape: {env.action_space.shape}")
    
    # Test reset
    print("\n🔄 Testing Environment Reset...")
    state, info = env.reset()
    print(f"   - Initial State Shape: {state.shape}")
    print(f"   - Initial State: {state}")
    print(f"   - Cargo Levels: {env.current_cargo}")
    
    # Test step with random actions
    print("\n🎲 Testing Random Actions...")
    for step in range(5):
        # Random actions for all trains
        actions = env.action_space.sample()
        print(f"\nDay {step + 1}:")
        print(f"   - Actions: {actions}")
        
        # Execute step
        next_state, reward, done, truncated, info = env.step(actions)
        
        print(f"   - Reward: {reward:.2f}")
        print(f"   - Done: {done}")
        print(f"   - Available Trains: {env.available_trains}")
        
        # Show train status
        active_trains = [t for t in env.trains if t['state'] != 0]  # 0 = IDLE
        print(f"   - Active Trains: {len(active_trains)}")
        
        env.render()
        
        state = next_state
        
        if done or truncated:
            print(f"   - Episode completed!")
            break
    
    # Test performance metrics
    print("\n📊 Performance Metrics:")
    metrics = env.get_performance_metrics()
    for key, value in metrics.items():
        print(f"   - {key}: {value}")
    
    print("\n✅ Multi-Route Environment Test Complete!")


def test_action_space():
    """Test the enhanced action space"""
    
    print("\n🎯 Testing Action Space...")
    
    env = MultiRouteTazaraEnv(num_trains=3)
    
    # Test different action combinations
    test_actions = [
        [0, 0, 0],  # All trains idle
        [1, 2, 3],  # Each train on different route
        [1, 1, 1],  # All trains on same route
        [0, 1, 2],  # Mixed actions
    ]
    
    for i, actions in enumerate(test_actions):
        print(f"\nTest Action Set {i + 1}: {actions}")
        
        # Reset environment
        state, _ = env.reset()
        
        # Execute actions
        next_state, reward, done, truncated, info = env.step(actions)
        
        print(f"   - Reward: {reward:.2f}")
        print(f"   - Train States: {[t['state'] for t in env.trains]}")
        print(f"   - Train Routes: {[t['route'] for t in env.trains]}")


if __name__ == "__main__":
    test_environment()
    test_action_space()
