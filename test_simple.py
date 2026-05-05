#!/usr/bin/env python3
"""
Simple test to check if cargo fix is working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes.multi_route import MultiRouteRequest
from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv

def test_simple():
    """Test if cargo fix is working"""
    
    print("🧪 Simple Test...")
    print("=" * 50)
    
    # Test Pydantic model
    try:
        request_data = {
            "num_trains": 3,
            "max_days": 14,
            "use_deep_rl": False,
            "cargo_requirements": {
                "DAR_KAPIRI": 100,
                "DAR_MBEYA": 100,
                "KAPIRI_NDOLA": 99
            }
        }
        
        request = MultiRouteRequest(**request_data)
        print("✅ Pydantic model working!")
        print(f"📋 Cargo requirements: {request.cargo_requirements}")
        
        # Test environment
        env = MultiRouteTazaraEnv(
            num_trains=3,
            max_cargo=5000,
            cargo_requirements=request.cargo_requirements
        )
        print("✅ Environment working!")
        print(f"📋 Initial cargo: {env.current_cargo}")
        
        print("\n🎉 SUCCESS: All components working!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()
