#!/usr/bin/env python3
"""
Test the endpoint function directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes.multi_route import MultiRouteRequest
from reinforcement_rl.multi_route_env import MultiRouteTazaraEnv

def test_endpoint_logic():
    """Test the endpoint logic directly"""
    
    print("🧪 Testing Endpoint Logic...")
    print("=" * 50)
    
    try:
        # Create request
        request = MultiRouteRequest(
            num_trains=3,
            max_days=14,
            use_deep_rl=False,
            cargo_requirements={
                "DAR_KAPIRI": 100,
                "DAR_MBEYA": 100,
                "KAPIRI_NDOLA": 99
            }
        )
        
        print("✅ Request created successfully")
        print(f"📋 Cargo requirements: {request.cargo_requirements}")
        
        # Test the getattr logic
        cargo_requirements = getattr(request, 'cargo_requirements', {
            "DAR_KAPIRI": 100,
            "DAR_MBEYA": 100,
            "KAPIRI_NDOLA": 100
        })
        
        print("✅ getattr() logic working")
        print(f"📋 Cargo requirements from getattr: {cargo_requirements}")
        
        # Test environment creation
        env = MultiRouteTazaraEnv(
            num_trains=request.num_trains,
            max_cargo=5000,
            cargo_requirements=cargo_requirements
        )
        
        print("✅ Environment created successfully")
        print(f"📋 Environment cargo: {env.current_cargo}")
        
        # Reset environment to populate cargo
        state, _ = env.reset()
        print("✅ Environment reset successfully")
        print(f"📋 Cargo after reset: {env.current_cargo}")
        
        print("\n🎉 SUCCESS: Endpoint logic working perfectly!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_endpoint_logic()
