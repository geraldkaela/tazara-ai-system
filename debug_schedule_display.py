import requests
import json

print('🔍 DEBUGGING SCHEDULE DISPLAY ISSUE')
print('=' * 50)

# Test 1: Check if schedules exist
print('\n📋 Step 1: Check existing schedules')
try:
    response = requests.get('http://127.0.0.1:8000/alerts/schedules')
    if response.status_code == 200:
        schedules = response.json()
        print(f'✅ Found {len(schedules)} schedules')
        for i, s in enumerate(schedules):
            print(f'   {i+1}. {s.get("id", "N/A")} - {s.get("status", "N/A")} ({s.get("schedule_type", "N/A")})')
    else:
        print(f'❌ Error: {response.status_code}')
except Exception as e:
    print(f'❌ Error: {e}')

# Test 2: Check if alerts exist for schedules
print('\n🚨 Step 2: Check schedule alerts')
try:
    response = requests.get('http://127.0.0.1:8000/alerts/')
    if response.status_code == 200:
        alerts = response.json()
        schedule_alerts = [a for a in alerts if a.get('category') == 'schedule']
        print(f'✅ Found {len(schedule_alerts)} schedule alerts out of {len(alerts)} total alerts')
        
        for alert in schedule_alerts:
            print(f'   📋 {alert.get("schedule_id", "N/A")}: {alert.get("message", "N/A")}')
    else:
        print(f'❌ Error: {response.status_code}')
except Exception as e:
    print(f'❌ Error: {e}')

# Test 3: Check summary data
print('\n📊 Step 3: Check summary metrics')
try:
    response = requests.get('http://127.0.0.1:8000/alerts/summary')
    if response.status_code == 200:
        summary = response.json()
        schedules = summary.get('schedules', {})
        print(f'✅ Summary shows:')
        print(f'   Active: {schedules.get("active_schedules", 0)}')
        print(f'   Completed: {schedules.get("completed_schedules", 0)}')
        print(f'   RL Optimized: {schedules.get("rl_optimized_schedules", 0)}')
        print(f'   Total: {schedules.get("total_schedules", 0)}')
    else:
        print(f'❌ Error: {response.status_code}')
except Exception as e:
    print(f'❌ Error: {e}')

# Test 4: Create a new schedule and check immediately
print('\n🧪 Step 4: Create new schedule and verify')
new_schedule = {
    "schedule_type": "manual",
    "status": "draft",
    "routes": ["DAR_KAPIRI"],
    "trains_used": 2,
    "total_cargo": 500.0,
    "cargo_types": ["Copper"],
    "duration_days": 3
}

try:
    # Create schedule
    response = requests.post('http://127.0.0.1:8000/alerts/schedules/create', json=new_schedule)
    if response.status_code == 200:
        new_sched = response.json()
        new_id = new_sched.get("id")
        print(f'✅ Created new schedule: {new_id}')
        
        # Check schedules immediately
        response = requests.get('http://127.0.0.1:8000/alerts/schedules')
        if response.status_code == 200:
            schedules = response.json()
            print(f'✅ Now have {len(schedules)} schedules')
            
            # Check alerts immediately
            response = requests.get('http://127.0.0.1:8000/alerts/')
            if response.status_code == 200:
                alerts = response.json()
                schedule_alerts = [a for a in alerts if a.get('category') == 'schedule']
                new_alerts = [a for a in schedule_alerts if a.get('schedule_id') == new_id]
                print(f'✅ Found {len(new_alerts)} alerts for new schedule')
                
                for alert in new_alerts:
                    print(f'   📋 {alert.get("message", "N/A")}')
    else:
        print(f'❌ Error creating schedule: {response.status_code}')
        
except Exception as e:
    print(f'❌ Error: {e}')

print('\n🎯 POSSIBLE ISSUES:')
print('1. Frontend not refreshing after schedule creation')
print('2. Schedule created but alerts not generated')
print('3. Browser caching old data')
print('4. Frontend JavaScript error')
print('5. API endpoint not being called correctly')

print('\n🔧 SOLUTIONS:')
print('1. Refresh the alerts page manually')
print('2. Check browser console for JavaScript errors')
print('3. Verify network requests in browser dev tools')
print('4. Clear browser cache')
print('5. Check if schedule creation API is being called')
