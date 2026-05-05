#!/usr/bin/env python3
"""
Debug Multi-route Schedule Creation Error
"""

import requests
import json

def debug_multi_route_error():
    """Debug the 500 error in multi-route schedule creation"""
    print('🔍 DEBUGGING MULTI-ROUTE SCHEDULE CREATION ERROR')
    print('=' * 50)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test with minimal data to isolate the issue
    minimal_request = {
        "num_trains": 2,
        "max_days": 3,
        "cargo_requirements": {
            "DAR_KAPIRI": 100
        }
    }
    
    print(f'\n🧪 Testing with minimal request:')
    print(f'   Request: {minimal_request}')
    
    try:
        response = requests.post(
            f"{base_url}/multi-route/schedule",
            json=minimal_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f'   Status Code: {response.status_code}')
        
        if response.status_code == 200:
            print(f'   ✅ Success: {response.json()}')
        else:
            print(f'   ❌ Error: {response.status_code}')
            print(f'   Response: {response.text}')
            
    except Exception as e:
        print(f'   ❌ Exception: {e}')
    
    # Test alerts endpoint separately
    print(f'\n🧪 Testing alerts endpoint separately:')
    try:
        alerts_request = {
            "schedule_type": "manual",
            "status": "active",
            "routes": ["DAR_KAPIRI"],
            "trains_used": 2,
            "total_cargo": 100.0,
            "cargo_types": ["Copper"],
            "duration_days": 3,
            "financial_metrics": {
                "revenue_zmw": 100000.0,
                "total_cost_zmw": 50000.0,
                "net_profit_zmw": 50000.0
            }
        }
        
        response = requests.post(
            f"{base_url}/alerts/schedules/create",
            json=alerts_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f'   Status Code: {response.status_code}')
        
        if response.status_code == 200:
            print(f'   ✅ Alerts endpoint working')
        else:
            print(f'   ❌ Alerts endpoint error: {response.status_code}')
            print(f'   Response: {response.text}')
            
    except Exception as e:
        print(f'   ❌ Alerts endpoint exception: {e}')

if __name__ == "__main__":
    debug_multi_route_error()
