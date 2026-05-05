"""
Test the forecast API endpoint to see data source
"""

import urllib.request
import json

def test_forecast_api():
    """Test the forecast API endpoint"""
    print("🔍 TESTING FORECAST API")
    print("=" * 50)
    
    try:
        # Prepare the request data
        request_data = {
            "days_ahead": 7,
            "model_type": "lstm",
            "include_confidence": True
        }
        
        # Make the API call
        url = "http://127.0.0.1:8000/api/forecast/"
        data = json.dumps(request_data).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        print("✅ FORECAST API RESPONSE:")
        print(f"   - Status: {result.get('status', 'N/A')}")
        print(f"   - Model Used: {result.get('model_used', 'N/A')}")
        print(f"   - Forecast Date: {result.get('forecast_date', 'N/A')}")
        
        forecasts = result.get('forecasts', [])
        if forecasts:
            print(f"📊 FORECAST DATA ({len(forecasts)} days):")
            for i, forecast in enumerate(forecasts[:3]):  # Show first 3 days
                print(f"   - Day {i+1}: {forecast.get('date', 'N/A')} → {forecast.get('forecast_tons', 'N/A')} tons")
                if forecast.get('upper_bound') and forecast.get('lower_bound'):
                    print(f"     Confidence: {forecast.get('lower_bound', 'N/A')} - {forecast.get('upper_bound', 'N/A')} tons")
        
        summary = result.get('summary', {})
        if summary:
            print(f"\n📈 SUMMARY STATS:")
            print(f"   - Mean Forecast: {summary.get('mean_forecast', 'N/A')} tons")
            print(f"   - Min/Max: {summary.get('min_forecast', 'N/A')} - {summary.get('max_forecast', 'N/A')} tons")
            print(f"   - Last Observed: {summary.get('last_observed_value', 'N/A')} tons ({summary.get('last_observed_date', 'N/A')})")
        
        rationale = result.get('rationale', '')
        if rationale:
            print(f"\n🎯 RATIONALE: {rationale}")
            
        return True
        
    except urllib.error.URLError as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("   Make sure the server is running on http://127.0.0.1:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_forecast_api()
