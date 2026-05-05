import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_scaling():
    print("🧪 Testing Multi-Train Scaling & Model Selection...")
    
    # Test 1: 6 trains with Deep RL (Should succeed)
    payload_6_deep = {
        "num_trains": 6,
        "max_days": 7,
        "use_deep_rl": True,
        "cargo_requirements": {"DAR_KAPIRI": 500, "DAR_MBEYA": 500, "KAPIRI_NDOLA": 200}
    }
    resp1 = requests.post(f"{BASE_URL}/multi-route/schedule", json=payload_6_deep)
    if resp1.status_code == 200:
        print("✅ 6 trains with Deep RL: SUCCESS")
    else:
        print(f"❌ 6 trains with Deep RL: FAILED ({resp1.status_code}: {resp1.text})")

    # Test 2: 7 trains with Deep RL (Should fail with 400)
    payload_7_deep = {
        "num_trains": 7,
        "max_days": 7,
        "use_deep_rl": True,
        "cargo_requirements": {"DAR_KAPIRI": 500, "DAR_MBEYA": 500, "KAPIRI_NDOLA": 200}
    }
    resp2 = requests.post(f"{BASE_URL}/multi-route/schedule", json=payload_7_deep)
    if resp2.status_code == 400:
        print("✅ 7 trains with Deep RL: Correctly blocked with 400")
    else:
        print(f"❌ 7 trains with Deep RL: Unexpected status ({resp2.status_code})")

    # Test 3: 7 trains with Traditional AI (Should succeed)
    payload_7_trad = {
        "num_trains": 7,
        "max_days": 7,
        "use_deep_rl": False,
        "cargo_requirements": {"DAR_KAPIRI": 500, "DAR_MBEYA": 500, "KAPIRI_NDOLA": 200}
    }
    resp3 = requests.post(f"{BASE_URL}/multi-route/schedule", json=payload_7_trad)
    if resp3.status_code == 200:
        print("✅ 7 trains with Traditional AI: SUCCESS")
    else:
        print(f"❌ 7 trains with Traditional AI: FAILED ({resp3.status_code}: {resp3.text})")

if __name__ == "__main__":
    try:
        test_scaling()
    except Exception as e:
        print(f"Error running tests: {e}")
