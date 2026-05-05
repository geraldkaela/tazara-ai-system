import requests

# Check current schedules
try:
    response = requests.get('http://127.0.0.1:8000/alerts/schedules')
    if response.status_code == 200:
        schedules = response.json()
        print(f'Current schedules: {len(schedules)}')
        for s in schedules:
            print(f'  - {s.get("id", "N/A")}: {s.get("status", "N/A")} ({s.get("schedule_type", "N/A")})')
    else:
        print(f'Error getting schedules: {response.status_code}')
        
    # Check current alerts
    response = requests.get('http://127.0.0.1:8000/alerts/')
    if response.status_code == 200:
        alerts = response.json()
        print(f'Current alerts: {len(alerts)}')
        schedule_alerts = [a for a in alerts if a.get('category') == 'schedule']
        print(f'Schedule alerts: {len(schedule_alerts)}')
        for a in schedule_alerts:
            print(f'  - {a.get("id", "N/A")}: {a.get("message", "N/A")}')
    else:
        print(f'Error getting alerts: {response.status_code}')
        
except Exception as e:
    print(f'Error: {e}')
