import requests
import json

def test_auto_schedule():
    """Test auto-schedule endpoint"""
    url = "http://127.0.0.1:8000/priority/auto-schedule"
    headers = {"Content-Type": "application/json"}
    data = {
        "num_trains": 5,
        "max_days": 7,
        "include_all_pending": True,
        "max_orders": 10
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success', False)}")
            print(f"Message: {result.get('message', 'No message')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_auto_schedule()
