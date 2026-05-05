"""
Test Multi-Route API Endpoints
Phase 2 - Multi-route scheduling API
"""

import requests
import json

def test_multi_route_api():
    """Test multi-route scheduling API endpoints"""
    
    base_url = "http://127.0.0.1:8000/multi-route"
    
    print("🚂 Testing Multi-Route API")
    print("=" * 50)
    
    # Test 1: Check system status
    print("\n1. Checking multi-route system status...")
    try:
        response = requests.get(f"{base_url}/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Multi-route enabled: {status['multi_route_enabled']}")
            print(f"✅ Model trained: {status['model_trained']}")
            print(f"✅ Supported routes: {status['routes']}")
            print(f"✅ Capabilities: {len(status['capabilities'])} features")
        else:
            print(f"❌ Status check failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Create multi-route schedule
    print("\n2. Creating multi-route schedule...")
    schedule_request = {
        "num_trains": 4,
        "max_days": 7,
        "cargo_requirements": {
            "DAR_KAPIRI": 500,
            "DAR_MBEYA": 300,
            "KAPIRI_NDOLA": 200
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/schedule",
            json=schedule_request
        )
        if response.status_code == 200:
            schedule = response.json()
            print(f"✅ Schedule created: {schedule['schedule_id']}")
            print(f"✅ Total days: {schedule['total_days']}")
            print(f"✅ Trains used: {schedule['performance_metrics']['trains_used']}")
            print(f"✅ Cargo delivered: {schedule['performance_metrics']['total_cargo_delivered']:.0f} tons")
            print(f"✅ Net profit: ZMW {schedule['cost_breakdown_zmw']['net_profit_zmw']:,.2f}")
            print(f"✅ Efficiency: {schedule['efficiency_analysis']['cargo_per_train']:.1f} tons/train")
            
            # Show sample daily actions
            print(f"✅ Sample daily actions:")
            for day, actions in enumerate(schedule['daily_actions'][:3]):
                action_desc = []
                for i, action in enumerate(actions):
                    if action == 0:
                        action_desc.append(f"T{i+1}:IDLE")
                    else:
                        routes = ["DAR_KAPIRI", "DAR_MBEYA", "KAPIRI_NDOLA"]
                        action_desc.append(f"T{i+1}:{routes[action-1]}")
                print(f"   Day {day+1}: {', '.join(action_desc)}")
            
        else:
            print(f"❌ Schedule creation failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Upload and schedule (if Excel file exists)
    print("\n3. Testing upload and schedule...")
    try:
        with open("uploads/testAI.xlsx", "rb") as f:
            files = {"file": ("testAI.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            params = {"num_trains": 4, "max_days": 7}
            
            response = requests.post(
                f"{base_url}/upload-and-schedule",
                files=files,
                params=params
            )
            
            if response.status_code == 200:
                schedule = response.json()
                print(f"✅ Upload schedule created: {schedule['schedule_id']}")
                print(f"✅ Cargo delivered: {schedule['performance_metrics']['total_cargo_delivered']:.0f} tons")
                print(f"✅ Net profit: ZMW {schedule['cost_breakdown_zmw']['net_profit_zmw']:,.2f}")
            else:
                print(f"❌ Upload schedule failed: {response.text}")
                
    except FileNotFoundError:
        print("⚠️ testAI.xlsx not found, skipping upload test")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎯 Multi-Route API Test Complete!")
    print("📊 Available endpoints:")
    print("   - GET /multi-route/status")
    print("   - POST /multi-route/schedule")
    print("   - POST /multi-route/upload-and-schedule")
    print("   - GET /multi-route/compare/{schedule_id}")

if __name__ == "__main__":
    test_multi_route_api()
