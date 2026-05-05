#!/usr/bin/env python3
"""
TAZARA API Endpoint Tester
Tests actual API endpoints with real HTTP requests

Usage: python test_api_endpoints.py [--host HOST] [--port PORT]
"""

import requests
import json
import sys
import argparse
from datetime import datetime, timedelta

class APITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        
    def test_endpoint(self, method, endpoint, data=None, description=""):
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = self.session.get(url, timeout=10)
            elif method == "POST":
                response = self.session.post(url, json=data, timeout=10)
            else:
                response = self.session.request(method, url, json=data, timeout=10)
            
            success = response.status_code in [200, 201, 307]
            result = {
                "description": description,
                "endpoint": endpoint,
                "method": method,
                "status": response.status_code,
                "success": success,
                "response": response.json() if success and response.text else None
            }
            self.results.append(result)
            
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {description}: {method} {endpoint} - Status {response.status_code}")
            
            if success and result["response"]:
                print(f"   Response: {json.dumps(result['response'], indent=2)[:200]}...")
                
            return success
            
        except requests.exceptions.ConnectionError:
            print(f"❌ {description}: Connection failed - Is the server running?")
            self.results.append({
                "description": description,
                "endpoint": endpoint,
                "error": "Connection failed"
            })
            return False
        except Exception as e:
            print(f"❌ {description}: Error - {str(e)}")
            self.results.append({
                "description": description,
                "endpoint": endpoint,
                "error": str(e)
            })
            return False
    
    def run_all_tests(self):
        """Run all endpoint tests"""
        print("="*60)
        print("🚆 TAZARA API Endpoint Testing")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print("="*60)
        
        # Test 1: Health Check
        self.test_endpoint("GET", "/health", description="Health Check")
        
        # Test 2: API Root
        self.test_endpoint("GET", "/", description="API Root")
        
        # Test 3: Forecast Endpoint
        forecast_data = {
            "days_ahead": 7,
            "include_confidence": True,
            "model_type": "lstm"
        }
        self.test_endpoint("POST", "/api/forecast/", data=forecast_data, 
                          description="Demand Forecast")
        
        # Test 4: Risk Analysis
        risk_data = {
            "schedule_id": "test_001",
            "route": "DAR_KAPIRI",
            "planned_departure": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "historical_issues": [
                {"date": (datetime.utcnow() - timedelta(days=10)).isoformat(), 
                 "issue_type": "delay", 
                 "duration_minutes": 45}
            ]
        }
        self.test_endpoint("POST", "/api/risk/analyze", data=risk_data,
                          description="Risk Analysis")
        
        # Test 5: Labor Optimization
        labor_data = {
            "route": "DAR_KAPIRI",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "required_skills": ["advanced"],
            "shift_type": "day"
        }
        self.test_endpoint("POST", "/api/labor/optimize", data=labor_data,
                          description="Labor Optimization")
        
        # Test 6: Performance Trends
        self.test_endpoint("GET", "/api/analytics/performance-trends?days=30",
                          description="Performance Trends")
        
        # Print Summary
        print("\n" + "="*60)
        print("📊 Test Summary")
        print("="*60)
        passed = sum(1 for r in self.results if r.get("success"))
        total = len(self.results)
        print(f"Passed: {passed}/{total}")
        print(f"Failed: {total - passed}/{total}")
        
        if passed == total:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            return 1

def main():
    parser = argparse.ArgumentParser(description="Test TAZARA API Endpoints")
    parser.add_argument("--host", default="localhost", help="API host")
    parser.add_argument("--port", default=8000, type=int, help="API port")
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    tester = APITester(base_url)
    
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
