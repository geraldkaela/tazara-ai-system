#!/usr/bin/env python3
"""
Example: Create orders via API
"""

import requests
import json

def create_sample_orders():
    """Create sample orders via API"""
    
    base_url = "http://127.0.0.1:8000"
    
    # Sample orders to create
    sample_orders = [
        {
            "customer_name": "Mining Corp Zambia",
            "cargo_type": "Copper",
            "cargo_weight": 500.0,
            "origin_station": "Dar es Salaam",
            "destination_station": "Kapiri Mposhi",
            "priority_level": 1,  # High Priority
            "requested_departure_date": "2026-03-20",
            "notes": "Urgent copper shipment for smelter"
        },
        {
            "customer_name": "Tanzania Export Ltd",
            "cargo_type": "Containers",
            "cargo_weight": 300.0,
            "origin_station": "Dar es Salaam", 
            "destination_station": "Mbeya",
            "priority_level": 2,  # Medium Priority
            "requested_departure_date": "2026-03-22",
            "notes": "Regular container shipment"
        },
        {
            "customer_name": "Zambia Logistics",
            "cargo_type": "Fuel",
            "cargo_weight": 200.0,
            "origin_station": "Kapiri Mposhi",
            "destination_station": "Ndola",
            "priority_level": 3,  # Low Priority
            "notes": "Fuel distribution to northern region"
        }
    ]
    
    print("🚀 CREATING SAMPLE ORDERS")
    print("=" * 50)
    
    for i, order in enumerate(sample_orders, 1):
        print(f"\n📦 Order {i}: {order['customer_name']}")
        print(f"   Cargo: {order['cargo_weight']} tons {order['cargo_type']}")
        print(f"   Route: {order['origin_station']} → {order['destination_station']}")
        print(f"   Priority: {order['priority_level']} ({'High' if order['priority_level'] == 1 else 'Medium' if order['priority_level'] == 2 else 'Low'})")
        
        try:
            response = requests.post(
                f"{base_url}/api/workflow/orders",
                json=order,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ SUCCESS: Order {result['order_id']} created")
            else:
                print(f"   ❌ FAILED: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    print(f"\n🎉 COMPLETED: Created {len(sample_orders)} orders")
    print("\n📋 NEXT STEPS:")
    print("1. Refresh browser dashboard")
    print("2. Go to Orders tab")
    print("3. Select orders in Create Schedule tab")
    print("4. Click 'Load Orders into Schedule'")
    print("5. Create AI-optimized schedule")

if __name__ == "__main__":
    create_sample_orders()
