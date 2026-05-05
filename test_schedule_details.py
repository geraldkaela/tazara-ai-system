"""
Test Schedule Details Endpoint
Test the new schedule details functionality
"""

import urllib.request
import json

def test_schedule_details():
    """Test schedule details endpoint"""
    try:
        # First create an auto-schedule to get a schedule ID
        print("Creating auto-schedule...")
        url = "http://127.0.0.1:8000/priority/auto-schedule"
        data = {
            "num_trains": 5,
            "max_days": 7,
            "include_all_pending": True,
            "max_orders": 10
        }
        
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=json_data,
            headers={
                'Content-Type': 'application/json',
                'Content-Length': len(json_data)
            }
        )
        
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            result = json.loads(response_data)
            
            if result.get('success', False):
                schedule_id = result.get('schedule_id')
                print(f"Schedule created: {schedule_id}")
                
                # Now test the schedule details endpoint
                print(f"Getting details for schedule: {schedule_id}")
                details_url = f"http://127.0.0.1:8000/priority/auto-schedule/{schedule_id}"
                
                details_req = urllib.request.Request(details_url)
                with urllib.request.urlopen(details_req) as details_response:
                    details_data = details_response.read().decode('utf-8')
                    details_result = json.loads(details_data)
                    
                    if details_result.get('success', False):
                        print("Schedule Details:")
                        print(f"  Schedule ID: {details_result['schedule']['schedule_id']}")
                        print(f"  Total Cargo: {details_result['schedule']['total_cargo_delivered']} tons")
                        print(f"  Efficiency: {details_result['schedule']['efficiency_score']}")
                        print(f"  Daily Assignments: {len(details_result['daily_assignments'])}")
                        print(f"  Scheduled Orders: {len(details_result['scheduled_orders'])}")
                        
                        print("\nDaily Assignments:")
                        for assignment in details_result['daily_assignments']:
                            print(f"  Day {assignment['day']}: {assignment['train_id']} -> {assignment['route']} ({assignment['cargo_tons']} tons)")
                        
                        print("\nScheduled Orders:")
                        for order in details_result['scheduled_orders']:
                            print(f"  {order['order_id']}: {order['customer_name']} - {order['cargo_weight']} tons ({order['origin_station']} to {order['destination_station']})")
                        
                        print("\nSummary:")
                        summary = details_result['summary']
                        print(f"  Routes Used: {', '.join(summary['unique_routes'])}")
                        print(f"  Active Days: {', '.join(f'Day {d}' for d in summary['days_with_assignments'])}")
                        print(f"  Total Cargo Scheduled: {summary['total_cargo_scheduled']} tons")
                        
                        print("\nSchedule details working perfectly! ")
                        return True
                    else:
                        print(f"Failed to get schedule details: {details_result.get('message', 'Unknown error')}")
                        return False
            else:
                print(f"Failed to create schedule: {result.get('message', 'Unknown error')}")
                return False
                
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_schedule_details()
