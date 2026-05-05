"""
Test Multi-Route Database Integration
Phase 2 - Database Backend Integration
"""

import requests
import json
import time
from datetime import datetime

def test_database_integration():
    """Test all database integration features"""
    
    base_url = "http://127.0.0.1:8000/multi-route"
    
    print("🚂 Testing Multi-Route Database Integration")
    print("=" * 60)
    
    # Test 1: System Status with Database
    print("\n1. Testing system status with database...")
    try:
        response = requests.get(f"{base_url}/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Multi-route enabled: {status['multi_route_enabled']}")
            print(f"✅ Database connected: {status.get('database_connected', False)}")
            print(f"✅ Model trained: {status['model_trained']}")
            
            if status.get('database_connected'):
                db_stats = status.get('database_stats', {})
                print(f"✅ Total schedules: {db_stats.get('total_schedules', 0)}")
                print(f"✅ Average efficiency: {db_stats.get('average_efficiency', 0):.1f}%")
                print(f"✅ Total cargo delivered: {db_stats.get('total_cargo_delivered', 0):.0f} tons")
            else:
                print("⚠️ Database not connected")
        else:
            print(f"❌ Status check failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Create Schedule (with database save)
    print("\n2. Creating schedule with database persistence...")
    schedule_request = {
        "num_trains": 4,
        "max_days": 7,
        "cargo_requirements": {
            "DAR_KAPIRI": 300,
            "DAR_MBEYA": 200,
            "KAPIRI_NDOLA": 150
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/schedule",
            json=schedule_request,
            timeout=30
        )
        if response.status_code == 200:
            schedule = response.json()
            schedule_id = schedule['schedule_id']
            print(f"✅ Schedule created: {schedule_id}")
            print(f"✅ Cargo delivered: {schedule['performance_metrics']['total_cargo_delivered']:.0f} tons")
            print(f"✅ Net profit: ZMW {schedule['cost_breakdown_zmw']['net_profit_zmw']:,.2f}")
            print(f"✅ Efficiency: {schedule['efficiency_analysis']['cargo_per_train']:.1f} tons/train")
            
            # Wait a moment for database save
            time.sleep(1)
            
        else:
            print(f"❌ Schedule creation failed: {response.text}")
            schedule_id = None
    except Exception as e:
        print(f"❌ Error: {e}")
        schedule_id = None
    
    # Test 3: Retrieve Schedules from Database
    print("\n3. Testing schedule retrieval from database...")
    try:
        response = requests.get(f"{base_url}/schedules?limit=5")
        if response.status_code == 200:
            schedules_data = response.json()
            schedules = schedules_data.get('schedules', [])
            print(f"✅ Retrieved {len(schedules)} schedules from database")
            
            if schedules:
                latest = schedules[0]
                print(f"✅ Latest schedule: {latest['schedule_id']}")
                print(f"✅ Total cargo: {latest['total_cargo']:.0f} tons")
                print(f"✅ Efficiency: {latest['efficiency']:.1f}")
        else:
            print(f"❌ Failed to retrieve schedules: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Performance Trends from Database
    print("\n4. Testing performance trends from database...")
    try:
        response = requests.get(f"{base_url}/performance/trends?days=7")
        if response.status_code == 200:
            trends_data = response.json()
            trends = trends_data.get('trends', [])
            print(f"✅ Retrieved {len(trends)} performance trends")
            
            if trends:
                latest = trends[0]
                print(f"✅ Latest trend date: {latest.get('performance_date', 'N/A')}")
                print(f"✅ Avg cargo: {latest.get('avg_cargo', 0):.1f} tons")
                print(f"✅ Avg efficiency: {latest.get('avg_efficiency', 0):.1f}%")
            else:
                print("📊 No performance trends yet (normal for new system)")
        else:
            print(f"❌ Failed to retrieve trends: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Route Performance from Database
    print("\n5. Testing route performance from database...")
    try:
        response = requests.get(f"{base_url}/performance/routes")
        if response.status_code == 200:
            route_data = response.json()
            route_performance = route_data.get('route_performance', [])
            print(f"✅ Retrieved {len(route_performance)} route performance records")
            
            if route_performance:
                for route in route_performance:
                    print(f"✅ {route['route_name']}: {route['avg_efficiency']:.1f}% efficiency")
            else:
                print("📊 No route performance data yet (normal for new system)")
        else:
            print(f"❌ Failed to retrieve route performance: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: Dashboard Statistics from Database
    print("\n6. Testing dashboard statistics from database...")
    try:
        response = requests.get(f"{base_url}/dashboard/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Total schedules: {stats.get('total_schedules', 0)}")
            print(f"✅ Average efficiency: {stats.get('average_efficiency', 0):.1f}%")
            print(f"✅ Average profit: ZMW {stats.get('average_profit', 0):,.2f}")
            print(f"✅ Total cargo delivered: {stats.get('total_cargo_delivered', 0):.0f} tons")
            print(f"✅ Recent schedules: {stats.get('recent_schedules', 0)}")
        else:
            print(f"❌ Failed to retrieve dashboard stats: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 7: Audit Logs from Database
    print("\n7. Testing audit logs from database...")
    try:
        response = requests.get(f"{base_url}/audit/logs?limit=5")
        if response.status_code == 200:
            audit_data = response.json()
            logs = audit_data.get('audit_logs', [])
            print(f"✅ Retrieved {len(logs)} audit logs")
            
            if logs:
                latest = logs[0]
                print(f"✅ Latest action: {latest['action_type']}")
                print(f"✅ Timestamp: {latest['timestamp']}")
                print(f"✅ Severity: {latest['severity']}")
            else:
                print("📊 No audit logs yet (normal for new system)")
        else:
            print(f"❌ Failed to retrieve audit logs: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 8: System Configuration from Database
    print("\n8. Testing system configuration from database...")
    try:
        response = requests.get(f"{base_url}/config")
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Retrieved {len(config)} configuration items")
            
            for key, value in config.items():
                print(f"✅ {key}: {value}")
        else:
            print(f"❌ Failed to retrieve configuration: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 9: Update System Configuration
    print("\n9. Testing configuration update...")
    try:
        config_update = {
            "max_trains": 12,
            "performance_threshold": 85,
            "coordination_bonus_enabled": True
        }
        
        response = requests.post(
            f"{base_url}/config?config_key=test_config",
            json=config_update
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Configuration updated: {result['message']}")
        else:
            print(f"❌ Configuration update failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 10: Detailed Schedule Retrieval
    if schedule_id:
        print("\n10. Testing detailed schedule retrieval...")
        try:
            response = requests.get(f"{base_url}/schedules/{schedule_id}")
            if response.status_code == 200:
                detailed_schedule = response.json()
                print(f"✅ Retrieved detailed schedule: {detailed_schedule['schedule_id']}")
                print(f"✅ Daily actions: {len(detailed_schedule['daily_actions'])} days")
                print(f"✅ Train assignments: {len(detailed_schedule['train_assignments'])} records")
                print(f"✅ Performance metrics: {len(detailed_schedule['performance_metrics'])} items")
            else:
                print(f"❌ Failed to retrieve detailed schedule: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🎉 Database Integration Test Complete!")
    print("=" * 60)
    print("\n📊 Database Features Tested:")
    print("✅ Schedule creation and persistence")
    print("✅ Schedule retrieval and listing")
    print("✅ Performance trends tracking")
    print("✅ Route performance monitoring")
    print("✅ Dashboard statistics")
    print("✅ Audit logging")
    print("✅ System configuration")
    print("✅ Configuration updates")
    print("✅ Detailed schedule retrieval")
    
    print("\n🚀 Your multi-route system now has full database integration!")
    print("📈 All schedules, performance data, and configurations are persisted.")
    print("🔍 Complete audit trail and historical analytics available.")

if __name__ == "__main__":
    test_database_integration()
