import urllib.request
import json

def test_auto_schedule():
    """Test auto-schedule endpoint with urllib"""
    url = "http://127.0.0.1:8000/priority/auto-schedule"
    data = {
        "num_trains": 5,
        "max_days": 7,
        "include_all_pending": True,
        "max_orders": 10
    }
    
    try:
        # Create request
        json_data = json.dumps(data).encode('utf-8')
        
        # Create request
        req = urllib.request.Request(
            url,
            data=json_data,
            headers={
                'Content-Type': 'application/json',
                'Content-Length': len(json_data)
            }
        )
        
        # Send request
        with urllib.request.urlopen(req) as response:
            print(f"Status Code: {response.getcode()}")
            response_data = response.read().decode('utf-8')
            print(f"Response: {response_data}")
            
            # Parse JSON response
            try:
                result = json.loads(response_data)
                print(f"Success: {result.get('success', False)}")
                print(f"Message: {result.get('message', 'No message')}")
                print(f"Schedule ID: {result.get('schedule_id', 'None')}")
                print(f"Orders Scheduled: {result.get('orders_scheduled', 0)}")
                
                if result.get('success', False):
                    print("✅ Auto-schedule working!")
                else:
                    print(f"❌ Auto-schedule failed: {result.get('message', 'Unknown error')}")
                    
            except json.JSONDecodeError as je:
                print(f"JSON Parse Error: {je}")
                
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error Type: {type(e)}")
        print(f"Error Args: {e.args}")

if __name__ == "__main__":
    test_auto_schedule()
