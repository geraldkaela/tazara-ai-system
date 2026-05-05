#!/usr/bin/env python3
"""
Check if the trained model is working
"""

import pickle
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.multi_route_agent import MultiRouteAgent
from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv

def check_trained_model():
    """Check if the trained model is working"""
    
    print("🔍 Checking Trained Model...")
    print("=" * 50)
    
    # Check if model file exists
    model_path = "models/multi_route_agent.pkl"
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        return False
    
    try:
        # Load the model
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        print("✅ Model loaded successfully")
        print(f"📋 Model keys: {list(model_data.keys())}")
        print(f"📊 Q-table size: {len(model_data.get('q_table', {}))}")
        print()
        
        # Create agent and load model
        agent = MultiRouteAgent(
            state_bins=(10,) * 20,
            action_size=4
        )
        agent.load(model_path)
        
        print("✅ Agent loaded with trained model")
        print(f"📊 Exploration rate: {agent.exploration_rate}")
        print()
        
        # Test with environment
        env = MultiRouteTazaraEnv(
            num_trains=3,
            cargo_requirements={
                "DAR_KAPIRI": 1000,
                "DAR_MBEYA": 1000,
                "KAPIRI_NDOLA": 500
            }
        )
        
        print("🧪 Testing agent with large cargo amounts...")
        state, _ = env.reset()
        
        # Get actions
        actions = agent.select_action(state)
        print(f"📋 Initial actions: {actions}")
        
        # Take one step
        next_state, reward, done, truncated, info = env.step(actions)
        print(f"📊 First step reward: ZMW {reward:,.0f}")
        print(f"📦 Cargo delivered: {sum(env.cargo_delivered.values()):.0f} tons")
        
        # Check if any trains are working
        working_trains = sum(1 for action in actions if action != 3)  # 3 = IDLE
        print(f"🚂 Working trains: {working_trains} out of {len(actions)}")
        
        if working_trains > 0:
            print("✅ SUCCESS: Agent is working!")
        else:
            print("❌ ISSUE: Agent still choosing IDLE")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking model: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_trained_model()
