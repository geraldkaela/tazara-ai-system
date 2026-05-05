"""
Test the route performance API endpoint to see data source
"""

import requests
import json

def test_route_performance():
    """Test the route performance API endpoint"""
    print("🔍 TESTING ROUTE PERFORMANCE API")
    print("=" * 50)
    
    try:
        # Call the API endpoint
        response = requests.get("http://127.0.0.1:8000/multi-route/performance/routes")
        
        if response.status_code == 200:
            data = response.json()
            routes = data.get('route_performance', [])
            
            print(f"✅ API Response: {len(routes)} routes found")
            print(f"📊 First route data:")
            
            if routes:
                first_route = routes[0]
                print(f"   - Route: {first_route.get('route_name', 'N/A')}")
                print(f"   - Avg Efficiency: {first_route.get('avg_efficiency', 'N/A')}")
                print(f"   - Avg Cargo: {first_route.get('avg_cargo', 'N/A')}")
                print(f"   - Total Cargo: {first_route.get('total_cargo', 'N/A')}")
                print(f"   - Total Profit: {first_route.get('total_profit', 'N/A')}")
                
                # Check if this looks like sample data
                if first_route.get('avg_efficiency') in [85.5, 78.3, 65.2, 72.8, 58.6, 45.2]:
                    print("🎯 DATA SOURCE: Sample data (hardcoded values)")
                elif first_route.get('avg_efficiency') == 0:
                    print("🎯 DATA SOURCE: Empty/zero data")
                else:
                    print("🎯 DATA SOURCE: Real database data")
                
            print(f"\n📋 All Routes Summary:")
            for route in routes:
                print(f"   - {route.get('route_name', 'N/A')}: {route.get('avg_efficiency', 'N/A')} efficiency, {route.get('avg_cargo', 'N/A')} cargo")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("   Make sure the server is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_route_performance()
