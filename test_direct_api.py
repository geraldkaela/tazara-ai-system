#!/usr/bin/env python3
"""
Direct test of API without caching issues
"""

import requests
import json

def test_direct_api():
    """Test API directly"""
    
    print("🧪 Testing API Directly...")
    print("=" * 50)
    
    # Test data
    test_data = {
        "num_trains": 3,
        "max_days": 14,
        "use_deep_rl": False,
        "cargo_requirements": {
            "DAR_KAPIRI": 100,
            "DAR_MBEYA": 100,
            "KAPIRI_NDOLA": 99
        }
    }
    
    try:
        print("📤 Sending POST request...")
        response = requests.post(
            "http://127.0.0.1:8000/multi-route/schedule",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS: Schedule created!")
            print(f"📋 Schedule ID: {result.get('schedule_id', 'N/A')}")
            print(f"📊 Cargo Delivered: {result.get('performance_metrics', {}).get('total_cargo_delivered', 0)} tons")
            print(f"💰 Net Profit: ZMW {result.get('performance_metrics', {}).get('cost_breakdown_zmw', {}).get('net_profit_zmw', 0)}")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"📋 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_direct_api()
