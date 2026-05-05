import urllib.request
import urllib.parse
import time
import json

BASE_URL = "http://127.0.0.1:8000"
ENDPOINT = f"{BASE_URL}/api/forecast/"

payload = {
    "days_ahead": 7,
    "include_confidence": True,
    "model_type": "lstm"
}

def post_request(url, data):
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), 
                                 headers={'Content-Type': 'application/json'},
                                 method='POST')
    with urllib.request.urlopen(req) as response:
        return response.read(), response.status

def test_performance():
    print("Testing Forecasting API Performance (Zero-Dependency)...")
    
    # First call (should be slower as it loads the model)
    print("Call 1: Cold Load (this will take 5-10 seconds context-loading)...")
    start_time = time.time()
    try:
        res_body, status = post_request(ENDPOINT, payload)
        duration = time.time() - start_time
        print(f"Call 1 Results: {duration:.2f}s | Status: {status}")
    except Exception as e:
        print(f"Call 1 failed: {e}")
        print("Note: Make sure your server is running with 'python -m api.main'")
        return

    # Second call (should be much faster due to cache)
    print("Call 2: Cached Load...")
    start_time = time.time()
    try:
        res_body, status = post_request(ENDPOINT, payload)
        duration = time.time() - start_time
        print(f"Call 2 Results: {duration:.2f}s | Status: {status}")
        
        if duration < 1.0:
            print("\nSUCCESS: Cache is working! Response time dropped significantly.")
        else:
            print("\nWARNING: Speedup not as expected. Check server logs.")
            
    except Exception as e:
        print(f"Call 2 failed: {e}")

if __name__ == "__main__":
    test_performance()
