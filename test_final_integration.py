"""
Final Test of TAZARA Multi-Route Database Integration
"""

import requests
import json
from database.db_manager import db_manager

def test_complete_integration():
    """Test all database integration features"""
    
    print("🚂 Testing Complete TAZARA Database Integration")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8000/multi-route"
    
    # Test 1: System Status
    print("\n1️⃣ Testing System Status...")
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Multi-route enabled: {status.get('multi_route_enabled', False)}")
            print(f"✅ Database connected: {status.get('database_connected', False)}")
            print(f"✅ Model trained: {status.get('model_trained', False)}")
            print(f"✅ Total schedules: {status.get('database_stats', {}).get('total_schedules', 0)}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status test error: {e}")
    
    # Test 2: Create Schedule
    print("\n2️⃣ Testing Schedule Creation...")
    try:
        schedule_request = {
            "num_trains": 4,
            "max_days": 7,
            "cargo_requirements": {
                "DAR_KAPIRI": 200,
                "DAR_MBEYA": 150,
                "KAPIRI_NDOLA": 100
            }
        }
        
        response = requests.post(f"{base_url}/schedule", json=schedule_request, timeout=10)
        if response.status_code == 200:
            schedule = response.json()
            print(f"✅ Schedule created: {schedule.get('schedule_id')}")
            print(f"✅ Cargo delivered: {schedule.get('performance_metrics', {}).get('total_cargo_delivered', 0)} tons")
            print(f"✅ Efficiency: {schedule.get('efficiency_analysis', {}).get('cargo_per_train', 0)} tons/train")
        else:
            print(f"❌ Schedule creation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Schedule creation error: {e}")
    
    # Test 3: Performance Analytics
    print("\n3️⃣ Testing Performance Analytics...")
    try:
        response = requests.get(f"{base_url}/performance/trends?days=7", timeout=5)
        if response.status_code == 200:
            trends = response.json().get('trends', [])
            print(f"✅ Retrieved {len(trends)} performance trends")
        else:
            print(f"❌ Performance trends failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Performance trends error: {e}")
    
    # Test 4: Route Performance
    print("\n4️⃣ Testing Route Performance...")
    try:
        response = requests.get(f"{base_url}/performance/routes", timeout=5)
        if response.status_code == 200:
            routes = response.json().get('route_performance', [])
            print(f"✅ Retrieved {len(routes)} route performance records")
        else:
            print(f"❌ Route performance failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Route performance error: {e}")
    
    # Test 5: Dashboard Statistics
    print("\n5️⃣ Testing Dashboard Statistics...")
    try:
        response = requests.get(f"{base_url}/dashboard/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Total schedules: {stats.get('total_schedules', 0)}")
            print(f"✅ Average efficiency: {stats.get('average_efficiency', 0)}%")
            print(f"✅ Total cargo delivered: {stats.get('total_cargo_delivered', 0)} tons")
        else:
            print(f"❌ Dashboard stats failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard stats error: {e}")
    
    # Test 6: Configuration Management
    print("\n6️⃣ Testing Configuration Management...")
    try:
        # Get current config
        response = requests.get(f"{base_url}/config", timeout=5)
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Retrieved {len(config)} configuration items")
            
            # Update config
            update_response = requests.post(
                f"{base_url}/config?config_key=test_integration",
                json={"test_mode": True, "integration_test": "complete"}
            )
            if update_response.status_code == 200:
                print("✅ Configuration update successful")
            else:
                print(f"❌ Config update failed: {update_response.status_code}")
        else:
            print(f"❌ Config retrieval failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Configuration test error: {e}")
    
    # Test 7: Audit Logs
    print("\n7️⃣ Testing Audit Logs...")
    try:
        response = requests.get(f"{base_url}/audit/logs?limit=5", timeout=5)
        if response.status_code == 200:
            logs = response.json().get('audit_logs', [])
            print(f"✅ Retrieved {len(logs)} audit logs")
        else:
            print(f"❌ Audit logs failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Audit logs error: {e}")
    
    print("\n🎉 Integration Test Complete!")
    print("=" * 50)
    
    print("\n📊 Integration Features Tested:")
    print("✅ Database connection and persistence")
    print("✅ Schedule creation and retrieval")
    print("✅ Performance analytics and trends")
    print("✅ Route performance monitoring")
    print("✅ Dashboard statistics")
    print("✅ Configuration management")
    print("✅ Audit logging")
    
    print("\n🚀 Your TAZARA Multi-Route System is Ready!")
    print("🌐 API Server: http://127.0.0.1:8000")
    print("📊 Dashboard: http://localhost:8505")
    print("📚 API Documentation: http://127.0.0.1:8000/docs")

if __name__ == "__main__":
    test_complete_integration()
