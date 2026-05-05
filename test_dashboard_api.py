"""Test analytics dashboard API endpoints."""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_dashboard_endpoints():
    """Test all dashboard endpoints."""
    
    endpoints = [
        ("/api/dashboard/health", "Dashboard Health Check"),
        ("/api/dashboard/overview", "Complete Overview"),
        ("/api/dashboard/risk", "Risk Analysis"),
        ("/api/dashboard/fragility", "Fragility Analysis"),
        ("/api/dashboard/bottlenecks", "Bottleneck Analysis"),
        ("/api/dashboard/scenarios", "What-if Scenarios"),
        ("/api/dashboard/models", "Model Performance"),
    ]
    
    print("\n" + "="*80)
    print("ANALYTICS DASHBOARD API TEST")
    print("="*80)
    
    all_passed = True
    results = []
    
    for endpoint, name in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ {name}")
                print(f"   Endpoint: {endpoint}")
                print(f"   Status: {response.status_code}")
                
                # Show sample from response
                if "data" in data:
                    print(f"   Records: {len(data.get('data', []))}")
                elif "tables" in data:
                    for table, info in data["tables"].items():
                        print(f"      {table}: {info['rows']} rows")
                else:
                    # Show first few keys
                    keys = list(data.keys())[:3]
                    print(f"   Keys: {', '.join(keys)}")
                
                results.append((name, "PASS"))
            else:
                print(f"\n❌ {name}")
                print(f"   Endpoint: {endpoint}")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text}")
                results.append((name, "FAIL"))
                all_passed = False
        
        except requests.exceptions.ConnectionError:
            print(f"\n⚠️  Cannot connect to {BASE_URL}")
            print("   Make sure the API server is running:")
            print("   python -m uvicorn api.main:app --reload")
            return False
        
        except Exception as e:
            print(f"\n❌ {name}")
            print(f"   Error: {str(e)}")
            results.append((name, "FAIL"))
            all_passed = False
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for name, status in results:
        symbol = "✅" if status == "PASS" else "❌"
        print(f"{symbol} {name}: {status}")
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ All dashboard endpoints working!")
        print("\nDashboard URLs:")
        for endpoint, name in endpoints:
            print(f"  • {name}: {BASE_URL}{endpoint}")
    else:
        print("❌ Some endpoints failed. Check server logs.")
    
    print("="*80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = test_dashboard_endpoints()
    sys.exit(0 if success else 1)
