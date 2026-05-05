#!/usr/bin/env python3
"""
Test the multi-route API endpoint
"""

import requests
import json

def test_multi_route_api():
    """Test the multi-route API with universal agent"""
    
    print("🧪 Testing Multi-Route API...")
    print("=" * 50)
    
    # Test data
    test_request = {
        "num_trains": 5,
        "max_days": 14,
        "use_deep_rl": False,
        "cargo_requirements": {
            "DAR_KAPIRI": 1000,
            "DAR_MBEYA": 1000,
            "KAPIRI_NDOLA": 1000
        }
    }
    
    try:
        print(f"📊 Sending request to API...")
        print(f"   - Trains: {test_request['num_trains']}")
        print(f"   - Days: {test_request['max_days']}")
        print(f"   - Cargo: {sum(test_request['cargo_requirements'].values())} tons")
        print(f"   - AI Model: {'Deep RL' if test_request['use_deep_rl'] else 'Universal AI'}")
        print()
        
        # Make the request
        response = requests.post(
            "http://127.0.0.1:8000/multi-route/schedule",
            json=test_request,
            timeout=30
        )
        
        print(f"📋 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS: API responded successfully!")
            print()
            print("📊 Results:")
            print(f"   - Schedule ID: {result.get('schedule_id', 'N/A')}")
            print(f"   - Cargo Delivered: {result.get('cargo_delivered', 0):.1f} tons")
            print(f"   - Total Profit: ZMW {result.get('total_profit', 0):,.0f}")
            print(f"   - Daily Assignments: {len(result.get('daily_assignments', []))} days")
            
            # Check if trains are working
            daily_assignments = result.get('daily_assignments', [])
            if daily_assignments:
                first_day = daily_assignments[0]
                train_assignments = first_day.get('train_assignments', [])
                working_trains = sum(1 for train in train_assignments if train.get('route') != 'IDLE')
                print(f"   - Working Trains (Day 1): {working_trains} out of {len(train_assignments)}")
                
                if working_trains > 0:
                    print("🎉 EXCELLENT: Trains are working and delivering cargo!")
                else:
                    print("⚠️  ISSUE: All trains are IDLE")
            else:
                print("⚠️  ISSUE: No daily assignments found")
                
        else:
            print(f"❌ ERROR: API returned {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server")
        print("   Make sure the server is running on http://127.0.0.1:8000")
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_multi_route_api()
