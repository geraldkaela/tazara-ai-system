"""
Debug Priority System
Test priority endpoints to identify issues
"""

import requests
import json
import sys

def test_priority_endpoints():
    """Test all priority endpoints"""
    base_url = "http://127.0.0.1:8000"
    
    print("🔍 Testing Priority System Endpoints")
    print("=" * 50)
    
    # Test 1: Priority queue status
    print("\n1. Testing /priority/queue/status")
    try:
        response = requests.get(f"{base_url}/priority/queue/status", timeout=5)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Priority queue list
    print("\n2. Testing /priority/queue/list")
    try:
        response = requests.get(f"{base_url}/priority/queue/list", timeout=5)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: Found {len(data.get('orders', []))} orders")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 3: Auto-schedule status
    print("\n3. Testing /priority/auto-schedule/status")
    try:
        response = requests.get(f"{base_url}/priority/auto-schedule/status", timeout=5)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 4: Debug scoring
    print("\n4. Testing /priority/debug/scoring")
    try:
        response = requests.get(f"{base_url}/priority/debug/scoring", timeout=5)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: Found {len(data.get('orders', []))} orders with scoring")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 5: Check if server is running
    print("\n5. Testing server root")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Server is running")
        else:
            print(f"   ❌ Server error: {response.text}")
    except Exception as e:
        print(f"   ❌ Server not accessible: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Debug Complete")

if __name__ == "__main__":
    test_priority_endpoints()
