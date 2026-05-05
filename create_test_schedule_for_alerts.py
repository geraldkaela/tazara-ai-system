#!/usr/bin/env python3
"""
Create Test Schedule for Alerts Display
"""

import requests
import json

def create_test_schedule():
    """Create a test schedule to verify alerts display"""
    print('🧪 CREATING TEST SCHEDULE FOR ALERTS DISPLAY')
    print('=' * 50)
    
    base_url = "http://127.0.0.1:8000"
    
    # Create a test schedule
    test_schedule = {
        "schedule_type": "manual",
        "status": "active",
        "routes": ["DAR_KAPIRI", "DAR_MBEYA"],
        "trains_used": 4,
        "total_cargo": 1000.0,
        "cargo_types": ["Copper", "Containers"],
        "duration_days": 5,
        "financial_metrics": {
            "revenue_zmw": 1200000.0,
            "total_cost_zmw": 600000.0,
            "net_profit_zmw": 600000.0
        },
        "completion_percentage": 30.0,
        "on_time_performance": 90.0
    }
    
    try:
        print(f'\n🚀 Creating test schedule...')
        response = requests.post(
            f"{base_url}/alerts/schedules/create",
            json=test_schedule,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            schedule = response.json()
            print(f'✅ Schedule created successfully!')
            print(f'   ID: {schedule.get("id", "N/A")}')
            print(f'   Type: {schedule.get("schedule_type", "N/A")}')
            print(f'   Status: {schedule.get("status", "N/A")}')
            print(f'   Routes: {schedule.get("routes", [])}')
            print(f'   Trains: {schedule.get("trains_used", 0)}')
            print(f'   Cargo: {schedule.get("total_cargo", 0):.0f} tons')
        else:
            print(f'❌ Error creating schedule: {response.status_code}')
            print(f'   Response: {response.text}')
            return False
            
    except Exception as e:
        print(f'❌ Exception: {e}')
        return False
    
    # Check if schedule appears in schedules list
    print(f'\n📋 Checking schedules list...')
    try:
        response = requests.get(f"{base_url}/alerts/schedules")
        schedules = response.json()
        print(f'   Total schedules: {len(schedules)}')
        
        for schedule in schedules:
            print(f'   📋 {schedule.get("id", "N/A")} - {schedule.get("status", "N/A")} ({schedule.get("schedule_type", "N/A")})')
            
    except Exception as e:
        print(f'❌ Error checking schedules: {e}')
    
    # Check if alerts were generated
    print(f'\n🚨 Checking alerts...')
    try:
        response = requests.get(f"{base_url}/alerts/")
        alerts = response.json()
        print(f'   Total alerts: {len(alerts)}')
        
        for alert in alerts:
            print(f'   🚨 {alert.get("severity", "N/A")}: {alert.get("message", "N/A")}')
            
    except Exception as e:
        print(f'❌ Error checking alerts: {e}')
    
    # Check updated summary
    print(f'\n📊 Checking summary...')
    try:
        response = requests.get(f"{base_url}/alerts/summary")
        summary = response.json()
        print(f'   Summary:')
        print(f'     Active schedules: {summary["schedules"]["active_schedules"]}')
        print(f'     Total schedules: {summary["schedules"]["total_schedules"]}')
        print(f'     Total alerts: {summary["alerts"]["total_alerts"]}')
        
    except Exception as e:
        print(f'❌ Error checking summary: {e}')
    
    print(f'\n🎉 TEST COMPLETE!')
    print(f'✅ If you see schedules and alerts above, the system is working!')
    print(f'🖥️  Refresh the alerts tab in your browser to see the schedules!')
    
    return True

if __name__ == "__main__":
    create_test_schedule()
