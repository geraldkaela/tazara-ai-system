import requests
import json

def test_alerts_api():
    """Test the alerts API endpoints"""
    base_url = "http://127.0.0.1:8000/alerts"
    
    print("🚨 Testing TAZARA Alerts API")
    print("=" * 50)
    
    # Test 1: Generate sample alerts
    print("\n1. Generating sample alerts...")
    try:
        response = requests.post(f"{base_url}/generate-sample")
        if response.status_code == 200:
            print(f"✅ Sample alerts generated: {response.json()}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get all alerts
    print("\n2. Fetching all alerts...")
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            alerts = response.json()
            print(f"✅ Found {len(alerts)} alerts")
            for alert in alerts[:3]:  # Show first 3
                print(f"   • {alert['severity'].upper()}: {alert['message']}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get alerts summary
    print("\n3. Getting alerts summary...")
    try:
        response = requests.get(f"{base_url}/summary")
        if response.status_code == 200:
            summary = response.json()
            print(f"✅ Summary: {summary}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Create daily report
    print("\n4. Creating daily report...")
    daily_report_data = {
        "date": "2026-02-05",
        "total_cargo_delivered": 700,
        "total_trains_used": 7,
        "delay_days": 0,
        "idle_days": 0,
        "net_profit_zmw": 0,
        "revenue_zmw": 35000,
        "total_cost_zmw": 35000,
        "efficiency_score": 85,
        "recommendations": [
            "Consider optimizing route selection for better profit margins",
            "Monitor KAPIRI_NDOLA route capacity utilization",
            "Review train scheduling efficiency"
        ]
    }
    
    try:
        response = requests.post(
            f"{base_url}/daily-report",
            json=daily_report_data
        )
        if response.status_code == 200:
            print(f"✅ Daily report created: {response.json()}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎯 Alerts API test completed!")
    print("📊 To view dashboard: python run_alerts_dashboard.py")
    print("🌐 Dashboard URL: http://localhost:8502")

if __name__ == "__main__":
    test_alerts_api()
