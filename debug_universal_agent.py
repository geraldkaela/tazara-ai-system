#!/usr/bin/env python3
"""
Debug universal agent loading in API context
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("🔍 Testing universal agent loading in API context...")
    
    # Import the load function
    from api.routes.multi_route import load_universal_agent
    
    # Test loading
    agent = load_universal_agent(5)
    
    if agent:
        print("✅ SUCCESS: Universal agent loaded in API context")
        print(f"   - Agent type: {type(agent)}")
        print(f"   - Exploration rate: {agent.exploration_rate}")
    else:
        print("❌ ERROR: Failed to load universal agent")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
