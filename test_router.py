#!/usr/bin/env python3
"""
Test if multi-route router can be imported and used
"""

import sys
import os

# Add the project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Try to import the router
    from api.routes.multi_route import router
    print("✅ SUCCESS: Multi-route router imported")
    print(f"   - Router type: {type(router)}")
    print(f"   - Router prefix: {router.prefix}")
    print(f"   - Router tags: {router.tags}")
    
    # Try to access the routes
    print("\n📋 Available routes:")
    for route in router.routes:
        print(f"   - {route.path}: {route.methods}")
        
except Exception as e:
    print(f"❌ ERROR: Failed to import multi-route router: {e}")
    import traceback
    traceback.print_exc()
