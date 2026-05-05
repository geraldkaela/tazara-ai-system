"""
Debug Routes Script
Check what routes are available and why priority routes aren't loading
"""

import requests
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def check_available_routes():
    """Check what routes are available"""
    try:
        response = requests.get("http://127.0.0.1:8000/docs", timeout=5)
        if response.status_code == 200:
            print("Available routes found in docs:")
            content = response.text
            
            # Look for common route patterns
            routes = []
            for line in content.split('\n'):
                if '/api/' in line or '/multi-route' in line or '/priority' in line:
                    routes.append(line.strip())
            
            if routes:
                print("Found these API routes:")
                for route in routes[:10]:  # Show first 10
                    print(f"  {route}")
            else:
                print("No specific API routes found in docs")
                
        else:
            print(f"Failed to get docs: {response.status_code}")
            
    except Exception as e:
        print(f"Error checking routes: {e}")

def test_basic_endpoints():
    """Test basic endpoints"""
    endpoints = [
        "/",
        "/health",
        "/api/forecast/",
        "/multi-route/schedule",
        "/priority/",
        "/priority/queue/status",
        "/priority/health"
    ]
    
    print("\nTesting endpoints:")
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://127.0.0.1:8000{endpoint}", timeout=5)
            status = "SUCCESS" if response.status_code == 200 else f"FAILED ({response.status_code})"
            print(f"  {endpoint}: {status}")
        except Exception as e:
            print(f"  {endpoint}: ERROR - {e}")

def check_server_logs():
    """Try to understand why priority routes aren't loading"""
    try:
        # Import the main app to check for errors
        from api.main import app
        
        print("\nChecking FastAPI app routes:")
        for route in app.routes:
            if hasattr(route, 'path'):
                print(f"  {route.path} - {route.methods if hasattr(route, 'methods') else 'N/A'}")
        
        return True
        
    except Exception as e:
        print(f"Error importing main app: {e}")
        return False

def main():
    """Main debug function"""
    print("TAZARA Routes Debug")
    print("=" * 40)
    
    # Check available routes
    check_available_routes()
    
    # Test basic endpoints
    test_basic_endpoints()
    
    # Check server logs
    check_server_logs()
    
    print("\n" + "=" * 40)
    print("Debug Complete!")

if __name__ == "__main__":
    main()
