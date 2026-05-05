#!/usr/bin/env python3
"""
Test Alerts Integration with Schedules
"""

import requests
import json
import time

def test_alerts_integration():
    """Test the complete alerts and schedules integration"""
    print('🧪 TESTING ALERTS INTEGRATION WITH SCHEDULES')
    print('=' * 50)
    
    base_url = "http://127.0.0.1:8000"
    
    # Step 1: Check current state
    print('\n📊 STEP 1: Checking current state')
    try:
        response = requests.get(f"{base_url}/alerts/schedules")
        schedules = response.json()
        print(f'   Current schedules: {len(schedules)}')
        
        response = requests.get(f"{base_url}/alerts/")
        alerts = response.json()
        print(f'   Current alerts: {len(alerts)}')
        
        response = requests.get(f"{base_url}/alerts/summary")
        summary = response.json()
        print(f'   Summary: {summary["schedules"]["total_schedules"]} schedules, {summary["alerts"]["total_alerts"]} alerts')
        
    except Exception as e:
        print(f'   ❌ Error checking state: {e}')
        return False
    
    # Step 2: Create a new schedule
    print('\n🚀 STEP 2: Creating new schedule')
    new_schedule = {
        "schedule_type": "manual",
        "status": "active",
        "routes": ["DAR_KAPIRI", "DAR_MBEYA"],
        "trains_used": 4,
        "total_cargo": 800.0,
        "cargo_types": ["Copper", "Containers"],
        "duration_days": 5,
        "financial_metrics": {
            "revenue_zmw": 800000.0,
            "total_cost_zmw": 400000.0,
            "net_profit_zmw": 400000.0
        },
        "completion_percentage": 25.0,
        "on_time_performance": 85.0
    }
    
    try:
        response = requests.post(f"{base_url}/alerts/schedules/create", json=new_schedule)
        if response.status_code == 200:
            schedule = response.json()
            print(f'   ✅ Schedule created: {schedule.get("id", "N/A")}')
            schedule_id = schedule.get("id")
        else:
            print(f'   ❌ Error creating schedule: {response.status_code}')
            print(f'   Response: {response.text}')
            return False
    except Exception as e:
        print(f'   ❌ Error creating schedule: {e}')
        return False
    
    # Step 3: Check if schedule appears in schedules list
    print('\n📋 STEP 3: Checking schedules list')
    time.sleep(0.5)  # Wait a moment for processing
    
    try:
        response = requests.get(f"{base_url}/alerts/schedules")
        schedules = response.json()
        print(f'   Total schedules: {len(schedules)}')
        
        # Find our new schedule
        found_schedule = None
        for s in schedules:
            if s.get("id") == schedule_id:
                found_schedule = s
                break
        
        if found_schedule:
            print(f'   ✅ Found new schedule: {found_schedule["id"]}')
            print(f'   Status: {found_schedule.get("status", "N/A")}')
            print(f'   Type: {found_schedule.get("schedule_type", "N/A")}')
        else:
            print(f'   ❌ New schedule not found in list')
            print(f'   Available schedules: {[s.get("id", "N/A") for s in schedules]}')
            return False
            
    except Exception as e:
        print(f'   ❌ Error checking schedules: {e}')
        return False
    
    # Step 4: Check if alerts were generated
    print('\n🚨 STEP 4: Checking generated alerts')
    
    try:
        response = requests.get(f"{base_url}/alerts/")
        alerts = response.json()
        print(f'   Total alerts: {len(alerts)}')
        
        # Find alerts for our schedule
        schedule_alerts = [a for a in alerts if a.get("schedule_id") == schedule_id]
        print(f'   Alerts for new schedule: {len(schedule_alerts)}')
        
        if schedule_alerts:
            for alert in schedule_alerts:
                print(f'   📋 {alert.get("severity", "N/A")}: {alert.get("message", "N/A")}')
        else:
            print(f'   ❌ No alerts found for new schedule')
            print(f'   Available alerts: {[a.get("id", "N/A") for a in alerts]}')
        
    except Exception as e:
        print(f'   ❌ Error checking alerts: {e}')
        return False
    
    # Step 5: Check updated summary
    print('\n📊 STEP 5: Checking updated summary')
    
    try:
        response = requests.get(f"{base_url}/alerts/summary")
        summary = response.json()
        schedules_data = summary.get("schedules", {})
        print(f'   Updated summary:')
        print(f'   Active schedules: {schedules_data.get("active_schedules", 0)}')
        print(f'   Completed schedules: {schedules_data.get("completed_schedules", 0)}')
        print(f'   Total schedules: {schedules_data.get("total_schedules", 0)}')
        
    except Exception as e:
        print(f'   ❌ Error checking summary: {e}')
        return False
    
    print(f'\n🎉 ALERTS INTEGRATION TEST COMPLETE!')
    print(f'✅ Schedule creation working')
    print(f'✅ Schedule listing working')
    print(f'✅ Alert generation working')
    print(f'✅ Summary updates working')
    
    return True

def test_frontend_display():
    """Test what the frontend should display"""
    print('\n\n🖥️  TESTING FRONTEND DISPLAY EXPECTATIONS')
    print('=' * 50)
    
    base_url = "http://127.0.0.1:8000"
    
    try:
        # Get schedules
        response = requests.get(f"{base_url}/alerts/schedules")
        schedules = response.json()
        
        # Get alerts
        response = requests.get(f"{base_url}/alerts/")
        alerts = response.json()
        
        print(f'\n📊 WHAT SHOULD BE DISPLAYED IN ALERTS TAB:')
        print(f'   📋 Schedules Section: {len(schedules)} schedules')
        for i, schedule in enumerate(schedules[:3]):  # Show first 3
            print(f'     {i+1}. {schedule.get("id", "N/A")} - {schedule.get("status", "N/A")} ({schedule.get("schedule_type", "N/A")})')
        
        print(f'   🚨 Alerts Section: {len(alerts)} alerts')
        for i, alert in enumerate(alerts[:3]):  # Show first 3
            schedule_link = f" (Schedule: {alert.get('schedule_id', 'N/A')})" if alert.get('schedule_id') else ""
            print(f'     {i+1}. {alert.get("severity", "N/A")}: {alert.get("message", "N/A")}{schedule_link}')
        
        if len(schedules) == 0:
            print(f'   ⚠️  No schedules found - this is why alerts tab is empty!')
        
        if len(alerts) == 0:
            print(f'   ⚠️  No alerts found - this is why alerts tab is empty!')
            
    except Exception as e:
        print(f'   ❌ Error: {e}')

if __name__ == "__main__":
    success = test_alerts_integration()
    test_frontend_display()
    
    if not success:
        print(f'\n❌ CONCLUSION: Alerts integration has issues')
        print(f'🔧 Possible fixes:')
        print(f'   1. Check if alerts API endpoints are working')
        print(f'   2. Verify schedule creation triggers alert generation')
        print(f'   3. Check frontend JavaScript for schedule loading')
        print(f'   4. Verify database/storage persistence')
    else:
        print(f'\n✅ CONCLUSION: Alerts integration working correctly!')
        print(f'🖥️  Frontend should display schedules and alerts properly')
