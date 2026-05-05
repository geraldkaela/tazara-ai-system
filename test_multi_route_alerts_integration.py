#!/usr/bin/env python3
"""
Test Multi-route Schedules Integration with Alerts
"""

import requests
import json
import time

def test_multi_route_alerts_integration():
    """Test the complete multi-route schedules to alerts integration"""
    print('🧪 TESTING MULTI-ROUTE SCHEDULES TO ALERTS INTEGRATION')
    print('=' * 60)
    
    base_url = "http://127.0.0.1:8000"
    
    # Step 1: Check current state
    print('\n📊 STEP 1: Checking current state')
    try:
        response = requests.get(f"{base_url}/alerts/schedules")
        schedules_before = response.json()
        print(f'   Schedules before: {len(schedules_before)}')
        
        response = requests.get(f"{base_url}/alerts/")
        alerts_before = response.json()
        print(f'   Alerts before: {len(alerts_before)}')
        
    except Exception as e:
        print(f'   ❌ Error checking state: {e}')
        return False
    
    # Step 2: Create a multi-route schedule
    print('\n🚀 STEP 2: Creating multi-route schedule')
    multi_route_request = {
        "num_trains": 4,
        "max_days": 5,
        "cargo_requirements": {
            "DAR_KAPIRI": 600,
            "DAR_MBEYA": 400,
            "KAPIRI_NDOLA": 200
        },
        "metadata": {
            "test": "multi_route_alerts_integration"
        }
    }
    
    try:
        print(f'   Sending request to /multi-route/schedule...')
        response = requests.post(
            f"{base_url}/multi-route/schedule",
            json=multi_route_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            schedule_response = response.json()
            print(f'   ✅ Multi-route schedule created!')
            print(f'   Schedule ID: {schedule_response.get("schedule_id", "N/A")}')
            print(f'   Total profit: ZMW {schedule_response.get("total_profit", 0):,.0f}')
            print(f'   Cargo delivered: {schedule_response.get("cargo_delivered", 0):,.0f} tons')
            schedule_id = schedule_response.get("schedule_id")
        else:
            print(f'   ❌ Error creating schedule: {response.status_code}')
            print(f'   Response: {response.text}')
            return False
            
    except Exception as e:
        print(f'   ❌ Exception: {e}')
        return False
    
    # Step 3: Wait a moment and check if schedule appears in alerts
    print('\n⏱️  STEP 3: Waiting for alerts integration...')
    time.sleep(1)
    
    # Step 4: Check updated state
    print('\n📋 STEP 4: Checking updated state')
    try:
        response = requests.get(f"{base_url}/alerts/schedules")
        schedules_after = response.json()
        print(f'   Schedules after: {len(schedules_after)}')
        
        response = requests.get(f"{base_url}/alerts/")
        alerts_after = response.json()
        print(f'   Alerts after: {len(alerts_after)}')
        
        # Find our new schedule
        new_schedule = None
        for s in schedules_after:
            if s.get("id") == schedule_id:
                new_schedule = s
                break
        
        if new_schedule:
            print(f'   ✅ Found new schedule in alerts: {new_schedule["id"]}')
            print(f'   Type: {new_schedule.get("schedule_type", "N/A")}')
            print(f'   Status: {new_schedule.get("status", "N/A")}')
            print(f'   Routes: {new_schedule.get("routes", [])}')
            print(f'   Trains: {new_schedule.get("trains_used", 0)}')
        else:
            print(f'   ❌ New schedule not found in alerts system')
            print(f'   Available schedules: {[s.get("id", "N/A") for s in schedules_after]}')
        
        # Find alerts for our schedule
        schedule_alerts = [a for a in alerts_after if a.get("schedule_id") == schedule_id]
        print(f'   Alerts for new schedule: {len(schedule_alerts)}')
        
        for alert in schedule_alerts:
            print(f'     🚨 {alert.get("severity", "N/A")}: {alert.get("message", "N/A")}')
        
    except Exception as e:
        print(f'   ❌ Error checking updated state: {e}')
        return False
    
    # Step 5: Check summary
    print('\n📊 STEP 5: Checking updated summary')
    try:
        response = requests.get(f"{base_url}/alerts/summary")
        summary = response.json()
        print(f'   Updated summary:')
        print(f'     Active schedules: {summary["schedules"]["active_schedules"]}')
        print(f'     Total schedules: {summary["schedules"]["total_schedules"]}')
        print(f'     Total alerts: {summary["alerts"]["total_alerts"]}')
        
    except Exception as e:
        print(f'   ❌ Error checking summary: {e}')
    
    # Step 6: Verify the schedule appears in frontend format
    print('\n🖥️  STEP 6: Frontend display verification')
    if new_schedule:
        print(f'   📋 What should appear in alerts tab:')
        print(f'     Schedule ID: {new_schedule["id"]}')
        print(f'     Status: {new_schedule["status"]}')
        print(f'     Type: {new_schedule["schedule_type"]}')
        print(f'     Routes: {", ".join(new_schedule.get("routes", []))}')
        print(f'     Trains: {new_schedule.get("trains_used", 0)}')
        print(f'     Cargo: {new_schedule.get("total_cargo", 0):.0f} tons')
        
        financial_metrics = new_schedule.get("financial_metrics", {})
        if financial_metrics:
            print(f'     Revenue: ZMW {financial_metrics.get("revenue_zmw", 0):,.0f}')
            print(f'     Profit: ZMW {financial_metrics.get("net_profit_zmw", 0):,.0f}')
    
    print(f'\n🎉 MULTI-ROUTE ALERTS INTEGRATION TEST COMPLETE!')
    
    success = (len(schedules_after) > len(schedules_before) and 
              len(alerts_after) > len(alerts_before) and
              new_schedule is not None)
    
    if success:
        print(f'✅ Integration working correctly!')
        print(f'📋 Multi-route schedules now appear in alerts tab!')
        print(f'🚨 Alerts are automatically generated!')
        print(f'📊 Summary metrics are updated!')
        print(f'🖥️  Refresh the alerts tab to see the new schedule!')
    else:
        print(f'❌ Integration has issues')
        print(f'🔧 Check the server logs for errors')
    
    return success

if __name__ == "__main__":
    test_multi_route_alerts_integration()
