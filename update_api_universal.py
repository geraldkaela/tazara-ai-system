#!/usr/bin/env python3
"""
Update API to use Universal AI Agent
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def update_api_universal():
    """Update API to use universal agent"""
    
    print("🔧 Updating API to use Universal AI Agent...")
    print("=" * 60)
    
    # Read the current API file
    api_file = "api/routes/multi_route.py"
    
    try:
        with open(api_file, 'r') as f:
            content = f.read()
        
        print("SUCCESS: API file loaded successfully")
        
        # Check if it's already updated
        if "multi_route_agent_universal.pkl" in content:
            print("API already using universal agent")
            return True
        
        # Update the model path to use universal agent
        old_model_path = 'MODEL_PATH = os.path.join(BASE_DIR, "models", "multi_route_agent.pkl")'
        new_model_path = 'MODEL_PATH = os.path.join(BASE_DIR, "models", "multi_route_agent_universal.pkl")'
        
        if old_model_path in content:
            content = content.replace(old_model_path, new_model_path)
            print("SUCCESS: Updated model path to universal agent")
        
        # Add universal agent loading logic
        universal_agent_code = '''
# Universal AI Agent - handles 1-12 trains
UNIVERSAL_MODEL_PATH = os.path.join(BASE_DIR, "models", "multi_route_agent_universal.pkl")

def load_universal_agent(num_trains):
    """Load universal agent that can handle any train count"""
    try:
        if os.path.exists(UNIVERSAL_MODEL_PATH):
            agent = MultiRouteAgent(
                state_bins=(10,) * 20,
                action_size=4
            )
            agent.load(UNIVERSAL_MODEL_PATH)
            agent.exploration_rate = 0.0  # No exploration in production
            print(f"SUCCESS: Universal agent loaded for {num_trains} trains")
            return agent
        else:
            print(f"ERROR: Universal agent not found at {UNIVERSAL_MODEL_PATH}")
            return None
    except Exception as e:
        print(f"ERROR: Failed to load universal agent: {e}")
        return None
'''
        
        # Insert the universal agent code after the imports
        import_end = content.find("DEEP_MODEL_PATH = os.path.join(BASE_DIR, \"models\", \"deep_multi_route_agent.pkl\")")
        if import_end != -1:
            insert_pos = content.find('\n', import_end) + 1
            content = content[:insert_pos] + universal_agent_code + content[insert_pos:]
            print("SUCCESS: Added universal agent loading logic")
        
        # Update the agent loading logic in create_schedule
        old_agent_loading = '''agent = MultiRouteAgent(
                state_bins=(10,) * 20,
                action_size=4
            )
            agent.load(MODEL_PATH)
            agent.exploration_rate = 0.0'''
        
        new_agent_loading = '''# Load universal agent that can handle any train count
            agent = load_universal_agent(request.num_trains)
            if agent is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"Universal AI model not found. Please train the universal agent first."
                )'''
        
        if old_agent_loading in content:
            content = content.replace(old_agent_loading, new_agent_loading)
            print("SUCCESS: Updated agent loading logic to use universal agent")
        
        # Write the updated content back
        with open(api_file, 'w') as f:
            f.write(content)
        
        print("SUCCESS: API updated successfully")
        print(f"Updated file: {api_file}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to update API: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if update_api_universal():
        print("\nAPI Update Complete!")
        print("SUCCESS: Universal agent integration ready")
        print("SUCCESS: Can handle 1-12 trains automatically")
        print("SUCCESS: Server restart required to apply changes")
    else:
        print("\nAPI Update Failed")
