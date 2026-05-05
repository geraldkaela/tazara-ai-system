#!/usr/bin/env python3
"""
Test AI with larger cargo amounts and more trains
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.multi_route_agent import MultiRouteAgent
from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv

def test_large_cargo():
    """Test AI with larger cargo amounts"""
    
    print("🧪 Testing AI with Large Cargo Amounts...")
    print("=" * 60)
    
    # Test scenarios
    scenarios = [
        {
            "name": "Small (3 trains, 300 tons)",
            "num_trains": 3,
            "cargo": {"DAR_KAPIRI": 100, "DAR_MBEYA": 100, "KAPIRI_NDOLA": 100}
        },
        {
            "name": "Large (5 trains, 2999 tons)",
            "num_trains": 5,
            "cargo": {"DAR_KAPIRI": 1000, "DAR_MBEYA": 999, "KAPIRI_NDOLA": 1000}
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📊 Testing: {scenario['name']}")
        print("-" * 40)
        
        try:
            # Create environment
            env = MultiRouteTazaraEnv(
                num_trains=scenario['num_trains'],
                cargo_requirements=scenario['cargo']
            )
            
            # Load trained agent
            agent = MultiRouteAgent(
                state_bins=(10,) * 20,
                action_size=4
            )
            agent.load('models/multi_route_agent.pkl')
            
            # Reset environment
            state, _ = env.reset()
            print(f"📋 Initial state: {state}")
            print(f"📦 Cargo available: {env.current_cargo}")
            
            # Get initial actions
            actions = agent.select_action(state)
            print(f"🚂 Initial actions: {actions}")
            
            # Check if any trains are working
            working_trains = sum(1 for action in actions if action != 3)  # 3 = IDLE
            print(f"🚂 Working trains: {working_trains} out of {len(actions)}")
            
            # Take first step
            next_state, reward, done, truncated, info = env.step(actions)
            print(f"📊 First step reward: ZMW {reward:,.0f}")
            print(f"📦 Cargo delivered: {sum(env.cargo_delivered.values()):.0f} tons")
            
            # Check if AI recognizes the cargo
            cargo_in_state = state[:3]  # First 3 values are cargo levels
            print(f"🔍 Cargo in state: {cargo_in_state}")
            
            if working_trains > 0:
                print("✅ SUCCESS: AI is working!")
            else:
                print("❌ ISSUE: AI choosing IDLE")
                print("🔍 Possible reasons:")
                print("  - Cargo amounts outside trained range")
                print("  - State space not recognized")
                print("  - Action space mismatch")
                print("  - Economics not understood")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n💡 Analysis:")
    print("If AI works with small cargo but not large cargo:")
    print("1. AI needs retraining with larger cargo amounts")
    print("2. State space needs to be adjusted")
    print("3. Economic model needs scaling")
    print("4. Training data needs more variety")

if __name__ == "__main__":
    test_large_cargo()
