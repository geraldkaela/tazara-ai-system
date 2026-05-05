#!/usr/bin/env python3
"""
Test if cargo override fix is working
"""

import requests
import json

def test_cargo_fix():
    """Test if cargo override fix is working"""
    
    print("🧪 Testing Cargo Override Fix...")
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
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Schedule created successfully!")
            print(f"📋 Schedule ID: {result.get('schedule_id', 'N/A')}")
            print(f"📊 Cargo Delivered: {result.get('performance_metrics', {}).get('total_cargo_delivered', 0)} tons")
            print(f"💰 Net Profit: ZMW {result.get('performance_metrics', {}).get('cost_breakdown_zmw', {}).get('net_profit_zmw', 0)}")
            
            # Check if trains are working
            daily_actions = result.get('daily_actions', [])
            working_trains = 0
            for day_action in daily_actions[:5]:  # Check first 5 days
                for action in day_action.get('train_assignments', []):
                    if action.get('route') != 'IDLE':
                        working_trains += 1
            
            print(f"🚂 Working Trains (first 5 days): {working_trains}")
            
            if working_trains > 0:
                print("🎉 SUCCESS: Trains are working!")
            else:
                print("❌ ISSUE: Trains still IDLE")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_cargo_fix()
