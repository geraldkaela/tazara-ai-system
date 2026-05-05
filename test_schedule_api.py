#!/usr/bin/env python3
"""
Test Multi-route Schedule API
"""

import requests
import json

def test_schedule_api():
    """Test the multi-route schedule API endpoint"""
    print('🧪 TESTING MULTI-ROUTE SCHEDULE API')
    print('=' * 50)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test data
    schedule_request = {
        "num_trains": 5,
        "max_days": 7,
        "cargo_requirements": {
            "DAR_KAPIRI": 800,
            "DAR_MBEYA": 400,
            "KAPIRI_NDOLA": 200
        },
        "metadata": {
            "test": "train_capacity_system"
        }
    }
    
    print(f'\n📋 Schedule Request:')
    print(f'   Trains: {schedule_request["num_trains"]}')
    print(f'   Days: {schedule_request["max_days"]}')
    print(f'   Cargo: {schedule_request["cargo_requirements"]}')
    print(f'   Total cargo: {sum(schedule_request["cargo_requirements"].values()):,} tons')
    
    try:
        print(f'\n🚀 Sending POST request to /multi-route/schedule')
        response = requests.post(
            f"{base_url}/multi-route/schedule",
            json=schedule_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f'   Status Code: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'   ✅ Schedule created successfully!')
            print(f'   Schedule ID: {data.get("schedule_id", "N/A")}')
            print(f'   Total Profit: ZMW {data.get("total_profit", 0):,.0f}')
            print(f'   Cargo Delivered: {data.get("cargo_delivered", 0):,.0f} tons')
            print(f'   Daily Assignments: {len(data.get("daily_assignments", []))} days')
            
            # Check cost breakdown
            cost_breakdown = data.get("cost_breakdown", {})
            if cost_breakdown:
                print(f'\n💰 Cost Breakdown:')
                print(f'   Revenue: ZMW {cost_breakdown.get("revenue_zmw", 0):,.0f}')
                print(f'   Total Cost: ZMW {cost_breakdown.get("total_cost_zmw", 0):,.0f}')
                print(f'   Net Profit: ZMW {cost_breakdown.get("net_profit_zmw", 0):,.0f}')
                print(f'   Profit Margin: {cost_breakdown.get("profit_margin_percent", 0):.1f}%')
            
            # Check efficiency analysis
            efficiency = data.get("efficiency_analysis", {})
            if efficiency:
                print(f'\n📊 Efficiency Analysis:')
                print(f'   Cargo per Train: {efficiency.get("cargo_per_train", 0):.1f} tons')
                print(f'   Profit per Train: ZMW {efficiency.get("profit_per_train", 0):,.0f}')
            
            print(f'\n🎉 SCHEDULE API WORKING!')
            
        else:
            print(f'   ❌ Error: {response.status_code}')
            print(f'   Response: {response.text}')
            
    except Exception as e:
        print(f'   ❌ Exception: {e}')

def test_fleet_api():
    """Test the train fleet API endpoints"""
    print('\n\n🚂 TESTING TRAIN FLEET API')
    print('=' * 50)
    
    base_url = "http://127.0.0.1:8000"
    
    try:
        # Test fleet endpoint
        print(f'\n📋 Testing /multi-route/fleet')
        response = requests.get(f"{base_url}/multi-route/fleet")
        
        if response.status_code == 200:
            data = response.json()
            print(f'   ✅ Fleet info retrieved')
            print(f'   Total trains: {data.get("total_trains", 0)}')
            print(f'   Total capacity: {data.get("total_capacity", 0):,} tons')
            print(f'   Daily operating cost: ZMW {data.get("daily_operating_cost", 0):,.0f}')
        else:
            print(f'   ❌ Error: {response.status_code}')
        
        # Test optimal trains endpoint
        print(f'\n🎯 Testing /multi-route/fleet/optimal/1000/DAR_KAPIRI')
        response = requests.get(f"{base_url}/multi-route/fleet/optimal/1000/DAR_KAPIRI")
        
        if response.status_code == 200:
            data = response.json()
            print(f'   ✅ Optimal trains retrieved')
            print(f'   Cargo request: {data.get("cargo_request", 0):,} tons')
            print(f'   Route: {data.get("route", "N/A")}')
            print(f'   Optimal trains: {len(data.get("optimal_trains", []))}')
            print(f'   Total capacity: {data.get("total_capacity", 0):,} tons')
            print(f'   Utilization: {data.get("capacity_utilization", 0):.1f}%')
        else:
            print(f'   ❌ Error: {response.status_code}')
            
    except Exception as e:
        print(f'   ❌ Exception: {e}')

if __name__ == "__main__":
    test_schedule_api()
    test_fleet_api()
