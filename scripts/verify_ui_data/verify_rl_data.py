import requests
import os
import sys

# Configuration
RL_API = "http://127.0.0.1:8000/multi-route/status"

def main():
    print("=" * 60)
    print("VERIFYING RL PERFORMANCE DATA (rl.html)")
    print("=" * 60)
    
    try:
        response = requests.get(RL_API)
        data = response.json()
        
        print(f"\nAPI Status: {data.get('status', 'Unknown')}")
        
        # RL Performance check
        supported = data.get('supported_trains', [])
        print(f"Supported Trains in Model: {len(supported)}")
        
        if len(supported) > 0:
            print("✅ PASS: RL model status and configuration fetched successfully.")
        else:
            print("❌ FAIL: RL model data empty or unavailable.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error fetching RL status: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
