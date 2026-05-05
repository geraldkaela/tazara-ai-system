import requests
import json

# Create a new test schedule
new_schedule = {
    "schedule_type": "rl_optimized",
    "status": "active",
    "routes": ["DAR_KAPIRI", "DAR_MBEYA", "KAPIRI_NDOLA"],
    "trains_used": 6,
    "total_cargo": 1500.0,
    "cargo_types": ["Copper", "Coal", "Containers"],
    "duration_days": 10,
    "financial_metrics": {
        "revenue_zmw": 1200000.0,
        "total_cost_zmw": 550000.0,
        "net_profit_zmw": 650000.0
    },
    "completion_percentage": 0.0,
    "on_time_performance": 100.0
}

try:
    print('🧪 Creating new test schedule...')
    response = requests.post('http://127.0.0.1:8000/alerts/schedules/create', json=new_schedule)
    
    if response.status_code == 200:
        schedule = response.json()
        print(f'✅ Schedule created successfully!')
        print(f'   ID: {schedule.get("id", "N/A")}')
        print(f'   Type: {schedule.get("schedule_type", "N/A")}')
        print(f'   Status: {schedule.get("status", "N/A")}')
        print(f'   Routes: {schedule.get("routes", [])}')
        print(f'   Trains: {schedule.get("trains_used", 0)}')
        print(f'   Cargo: {schedule.get("total_cargo", 0)} tons')
        
        # Check if alerts were generated
        print('\n🚨 Checking for new alerts...')
        alerts_response = requests.get('http://127.0.0.1:8000/alerts/')
        if alerts_response.status_code == 200:
            alerts = alerts_response.json()
            schedule_alerts = [a for a in alerts if a.get('category') == 'schedule']
            print(f'   Total alerts: {len(alerts)}')
            print(f'   Schedule alerts: {len(schedule_alerts)}')
            
            # Find alerts for our new schedule
            new_schedule_id = schedule.get("id")
            our_alerts = [a for a in schedule_alerts if a.get("schedule_id") == new_schedule_id]
            print(f'   Alerts for new schedule: {len(our_alerts)}')
            
            for alert in our_alerts:
                print(f'     - {alert.get("message", "N/A")}')
                
        print('\n📊 Checking updated schedules list...')
        schedules_response = requests.get('http://127.0.0.1:8000/alerts/schedules')
        if schedules_response.status_code == 200:
            schedules = schedules_response.json()
            print(f'   Total schedules: {len(schedules)}')
            for s in schedules:
                print(f'     - {s.get("id", "N/A")}: {s.get("status", "N/A")} ({s.get("schedule_type", "N/A")})')
                
    else:
        print(f'❌ Error creating schedule: {response.status_code}')
        print(f'   Response: {response.text}')
        
except Exception as e:
    print(f'❌ Error: {str(e)}')
