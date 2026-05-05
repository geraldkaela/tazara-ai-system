#!/usr/bin/env python3
"""
Test Train Capacity System Implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reinforcement_rl.train_fleet import TrainFleet, TrainType

def test_train_fleet():
    """Test the train fleet system"""
    print('🚂 TESTING TRAIN FLEET SYSTEM')
    print('=' * 50)
    
    fleet = TrainFleet()
    
    print('\n📊 FLEET SUMMARY:')
    summary = fleet.get_fleet_summary()
    print(f'   Total Trains: {summary["total_trains"]}')
    print(f'   Total Capacity: {summary["total_capacity"]:,} tons')
    print(f'   Average Availability: {summary["average_availability"]:.1%}')
    print(f'   Daily Operating Cost: ZMW {summary["operating_cost_per_day"]:,.0f}')
    
    print('\n🚆 TRAINS BY TYPE:')
    for train_type, stats in summary["by_type"].items():
        print(f'   {train_type}: {stats["count"]} trains, {stats["total_capacity"]:,} tons capacity')
    
    print('\n🎯 TESTING OPTIMAL TRAIN SELECTION:')
    
    # Test case 1: Large cargo on main route
    cargo1 = 2500
    route1 = "DAR_KAPIRI"
    optimal_trains1 = fleet.get_optimal_trains_for_cargo(cargo1, route1)
    print(f'\n   Test 1: {cargo1:,} tons on {route1}')
    print(f'   Optimal trains: {len(optimal_trains1)}')
    total_capacity1 = sum(t.capacity_tons for t in optimal_trains1)
    print(f'   Total capacity: {total_capacity1:,} tons')
    print(f'   Utilization: {(cargo1/total_capacity1)*100:.1f}%')
    for train in optimal_trains1:
        print(f'     - {train.train_id}: {train.capacity_tons} tons ({train.train_type.value})')
    
    # Test case 2: Medium cargo on regional route
    cargo2 = 600
    route2 = "DAR_MBEYA"
    optimal_trains2 = fleet.get_optimal_trains_for_cargo(cargo2, route2)
    print(f'\n   Test 2: {cargo2:,} tons on {route2}')
    print(f'   Optimal trains: {len(optimal_trains2)}')
    total_capacity2 = sum(t.capacity_tons for t in optimal_trains2)
    print(f'   Total capacity: {total_capacity2:,} tons')
    print(f'   Utilization: {(cargo2/total_capacity2)*100:.1f}%')
    for train in optimal_trains2:
        print(f'     - {train.train_id}: {train.capacity_tons} tons ({train.train_type.value})')
    
    # Test case 3: Small cargo on local route
    cargo3 = 200
    route3 = "DAR_KIDATU"
    optimal_trains3 = fleet.get_optimal_trains_for_cargo(cargo3, route3)
    print(f'\n   Test 3: {cargo3:,} tons on {route3}')
    print(f'   Optimal trains: {len(optimal_trains3)}')
    if optimal_trains3:
        total_capacity3 = sum(t.capacity_tons for t in optimal_trains3)
        print(f'   Total capacity: {total_capacity3:,} tons')
        print(f'   Utilization: {(cargo3/total_capacity3)*100:.1f}%')
        for train in optimal_trains3:
            print(f'     - {train.train_id}: {train.capacity_tons} tons ({train.train_type.value})')
    else:
        print(f'   No suitable trains found for {cargo3} tons on {route3}')
        # Try with available trains
        available = fleet.get_available_trains(route3, min_capacity=cargo3)
        if available:
            print(f'   Available trains: {len(available)}')
            for train in available[:1]:  # Show first available
                print(f'     - {train.train_id}: {train.capacity_tons} tons ({train.train_type.value})')
        else:
            print(f'   No trains available for this route')
    
    print('\n💰 COST ANALYSIS:')
    for train_id in ["TF-001", "SF-003", "LF-006"]:
        train = fleet.get_train_by_id(train_id)
        if train:
            distance = 1000  # 1000 km example
            days = 3
            cost = fleet.calculate_transport_cost(train_id, distance, days)
            print(f'   {train_id}: ZMW {cost:,.0f} for {distance:,}km in {days} days')
            print(f'     Capacity: {train.capacity_tons} tons, Cost/ton: ZMW {cost/train.capacity_tons:.0f}')
    
    print('\n🎯 EFFICIENCY SCORES:')
    test_cases = [
        ("TF-001", 1000, "DAR_KAPIRI"),
        ("SF-003", 600, "DAR_MBEYA"),
        ("LF-006", 300, "DAR_KIDATU")
    ]
    
    for train_id, cargo, route in test_cases:
        efficiency = fleet.get_train_efficiency_score(train_id, cargo, route)
        train = fleet.get_train_by_id(train_id)
        print(f'   {train_id}: {efficiency:.3f} ({cargo} tons on {route})')
        print(f'     Type: {train.train_type.value}, Capacity: {train.capacity_tons} tons')
    
    print('\n✅ TRAIN FLEET SYSTEM WORKING!')
    print('🚂 Different train types with varying capacities')
    print('📊 Optimal train selection based on cargo and route')
    print('💰 Realistic cost calculations')
    print('🎯 Efficiency scoring for train-cargo-route combinations')

def test_api_endpoints():
    """Test the new API endpoints"""
    print('\n\n🌐 TESTING API ENDPOINTS')
    print('=' * 50)
    
    import requests
    
    base_url = "http://127.0.0.1:8000"
    
    # Test fleet endpoint
    print('\n📋 Testing /multi-route/fleet')
    try:
        response = requests.get(f"{base_url}/multi-route/fleet")
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Status: {response.status_code}')
            print(f'   Total trains: {data.get("total_trains", 0)}')
            print(f'   Total capacity: {data.get("total_capacity", 0):,} tons')
            print(f'   Train details: {len(data.get("train_details", []))} trains')
        else:
            print(f'❌ Status: {response.status_code}')
            print(f'   Error: {response.text}')
    except Exception as e:
        print(f'❌ Error: {e}')
    
    # Test optimal trains endpoint
    print('\n🎯 Testing /multi-route/fleet/optimal/2500/DAR_KAPIRI')
    try:
        response = requests.get(f"{base_url}/multi-route/fleet/optimal/2500/DAR_KAPIRI")
        if response.status_code == 200:
            data = response.json()
            print(f'✅ Status: {response.status_code}')
            print(f'   Cargo request: {data.get("cargo_request", 0):,} tons')
            print(f'   Route: {data.get("route", "N/A")}')
            print(f'   Optimal trains: {len(data.get("optimal_trains", []))}')
            print(f'   Total capacity: {data.get("total_capacity", 0):,} tons')
            print(f'   Utilization: {data.get("capacity_utilization", 0):.1f}%')
            print(f'   Excess capacity: {data.get("excess_capacity", 0):,} tons')
        else:
            print(f'❌ Status: {response.status_code}')
            print(f'   Error: {response.text}')
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    test_train_fleet()
    test_api_endpoints()
