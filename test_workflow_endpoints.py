"""
Test script for new workflow endpoints
Tests all the newly implemented features
"""

import requests
import json
from datetime import date, datetime

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(method, endpoint, data=None, params=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url, params=params)
        
        print(f"\n{'='*60}")
        print(f"🧪 {method} {endpoint}")
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS")
            if response.text:
                try:
                    data = response.json()
                    print(f"📄 Response: {json.dumps(data, indent=2)[:500]}...")
                except:
                    print(f"📄 Response: {response.text[:500]}...")
        else:
            print("❌ FAILED")
            print(f"📄 Error: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False

def run_tests():
    """Run all workflow endpoint tests"""
    print("🚀 Testing TAZARA Workflow Endpoints")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Base URL: {BASE_URL}")
    
    test_results = []
    
    # Test 1: Health Check
    test_results.append(test_endpoint("GET", "/health"))
    
    # Test 2: Get scheduling priorities
    test_results.append(test_endpoint("GET", "/api/workflow/priorities"))
    
    # Test 3: Get scheduling rules
    test_results.append(test_endpoint("GET", "/api/workflow/rules"))
    
    # Test 4: Create customer order
    order_data = {
        "customer_name": "Test Customer",
        "cargo_type": "Coal",
        "cargo_weight": 500.0,
        "origin_station": "Dar es Salaam",
        "destination_station": "Kapiri Mposhi",
        "priority_level": 2,
        "requested_departure_date": date.today().isoformat(),
        "notes": "Test order for workflow"
    }
    test_results.append(test_endpoint("POST", "/api/workflow/orders", order_data))
    
    # Test 5: Get customer orders
    test_results.append(test_endpoint("GET", "/api/workflow/orders"))
    
    # Test 6: Get existing schedules
    test_results.append(test_endpoint("GET", "/multi-route/schedules"))
    
    # Test 7: Get configuration (enhanced with priorities)
    test_results.append(test_endpoint("GET", "/api/config"))
    
    # Test 8: Validate schedule against rules
    test_schedule_data = {
        "cargo_requirements": {"DAR_KAPIRI": 1000},
        "daily_actions": {"day_1": {"train_1": {"departure_time": "08:00"}}}
    }
    test_results.append(test_endpoint("POST", "/api/workflow/rules/validate", test_schedule_data))
    
    # Test 9: Get system info
    test_results.append(test_endpoint("GET", "/system/info"))
    
    # Test 10: Get dashboard stats
    test_results.append(test_endpoint("GET", "/multi-route/dashboard/stats"))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Workflow endpoints are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")
    
    print("\n📋 New Features Tested:")
    print("   • Customer order management")
    print("   • Scheduling priorities")
    print("   • Rules and constraints")
    print("   • Configuration enhancements")
    print("   • API integration")
    
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
