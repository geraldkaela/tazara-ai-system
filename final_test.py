#!/usr/bin/env python3
"""
Final test of Universal AI System
"""

import requests
import json

def test_universal_ai():
    """Test the universal AI system with various train counts"""
    
    print("🎉 FINAL TEST OF UNIVERSAL AI SYSTEM")
    print("=" * 60)
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Small Operation",
            "trains": 3,
            "cargo": {"DAR_KAPIRI": 500, "DAR_MBEYA": 500, "KAPIRI_NDOLA": 500}
        },
        {
            "name": "Medium Operation", 
            "trains": 5,
            "cargo": {"DAR_KAPIRI": 1000, "DAR_MBEYA": 1000, "KAPIRI_NDOLA": 1000}
        },
        {
            "name": "Large Operation",
            "trains": 8,
            "cargo": {"DAR_KAPIRI": 1500, "DAR_MBEYA": 1500, "KAPIRI_NDOLA": 1500}
        },
        {
            "name": "Maximum Operation",
            "trains": 12,
            "cargo": {"DAR_KAPIRI": 2000, "DAR_MBEYA": 2000, "KAPIRI_NDOLA": 2000}
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        print(f"   - Trains: {scenario['trains']}")
        print(f"   - Total Cargo: {sum(scenario['cargo'].values())} tons")
        
        try:
            response = requests.post(
                "http://127.0.0.1:8000/multi-route/schedule",
                json={
                    "num_trains": scenario['trains'],
                    "max_days": 14,
                    "use_deep_rl": False,
                    "cargo_requirements": scenario['cargo']
                },
                timeout=30
            )
            
            print(f"   - Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                cargo_delivered = result.get('cargo_delivered', 0)
                total_profit = result.get('total_profit', 0)
                
                print(f"   - Cargo Delivered: {cargo_delivered:.1f} tons")
                print(f"   - Total Profit: ZMW {total_profit:,.0f}")
                
                if cargo_delivered > 0:
                    print("   ✅ SUCCESS: AI is working and delivering cargo!")
                else:
                    print("   ⚠️  ISSUE: AI not delivering cargo")
                    
            else:
                print(f"   - Response: {response.text}")
                
        except Exception as e:
            print(f"   - ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 UNIVERSAL AI SYSTEM TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_universal_ai()
