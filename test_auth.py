"""
Test Authentication System
Verify login and token generation work correctly
"""

import requests
import json

def test_auth():
    """Test authentication endpoints"""
    base_url = "http://127.0.0.1:8000"
    
    print("🔐 Testing TAZARA Authentication System")
    print("=" * 50)
    
    # Test login
    print("\n1. Testing login endpoint...")
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    
    try:
        response = requests.post(f"{base_url}/auth/token", data=login_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Login successful!")
            print(f"   Token Type: {token_data.get('token_type')}")
            print(f"   Role: {token_data.get('role')}")
            print(f"   Expires In: {token_data.get('expires_in')} seconds")
            
            # Test protected endpoint with token
            print("\n2. Testing protected endpoint...")
            headers = {"Authorization": f"Bearer {token_data.get('access_token')}"}
            
            me_response = requests.get(f"{base_url}/auth/me", headers=headers)
            print(f"Status Code: {me_response.status_code}")
            
            if me_response.status_code == 200:
                user_data = me_response.json()
                print(f"✅ Protected endpoint access successful!")
                print(f"   Username: {user_data.get('username')}")
                print(f"   Email: {user_data.get('email')}")
                print(f"   Role: {user_data.get('role')}")
                
                # Test permissions endpoint
                print("\n3. Testing permissions endpoint...")
                perms_response = requests.get(f"{base_url}/auth/me/permissions", headers=headers)
                print(f"Status Code: {perms_response.status_code}")
                
                if perms_response.status_code == 200:
                    perms_data = perms_response.json()
                    print(f"✅ Permissions endpoint successful!")
                    print(f"   Role: {perms_data.get('role')}")
                    print(f"   Features: {list(perms_data.get('features', {}).keys())}")
                    
                    # Test auto-scheduler endpoint (should require RUN_SCHEDULER permission)
                    print("\n4. Testing auto-scheduler endpoint...")
                    auto_schedule_data = {
                        "num_trains": 5,
                        "max_days": 7,
                        "max_orders": 10
                    }
                    
                    schedule_response = requests.post(
                        f"{base_url}/priority/auto-schedule", 
                        json=auto_schedule_data,
                        headers=headers
                    )
                    print(f"Status Code: {schedule_response.status_code}")
                    
                    if schedule_response.status_code == 200:
                        schedule_data = schedule_response.json()
                        print(f"✅ Auto-scheduler access successful!")
                        print(f"   Success: {schedule_data.get('success')}")
                        print(f"   Orders Scheduled: {schedule_data.get('orders_scheduled')}")
                    else:
                        print(f"❌ Auto-scheduler access failed: {schedule_response.text}")
                else:
                    print(f"❌ Permissions endpoint failed: {perms_response.text}")
            else:
                print(f"❌ Protected endpoint access failed: {me_response.text}")
        else:
            print(f"❌ Login failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("   Make sure the server is running on http://127.0.0.1:8000")

if __name__ == "__main__":
    test_auth()
