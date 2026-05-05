import requests

url = "http://127.0.0.1:8000/upload/"
file_path = "uploads/testAI.xlsx"

try:
    with open(file_path, "rb") as f:
        files = {"file": ("testAI.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        headers = {"accept": "application/json"}
        
        response = requests.post(url, files=files, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ ZMW Cost Analysis Results:")
            print(f"Routes detected: {data['routes_detected']}")
            print(f"Routes used: {data['routes_used']}")
            
            cost_breakdown = data['evaluation']['cost_breakdown_zmw']
            print(f"\n🇿🇲 Financial Breakdown:")
            print(f"  Revenue: ZMW {cost_breakdown['revenue_zmw']:,.2f}")
            print(f"  Train Operating Cost: ZMW {cost_breakdown['train_cost_zmw']:,.2f}")
            print(f"  Delay Cost: ZMW {cost_breakdown['delay_cost_zmw']:,.2f}")
            print(f"  Idle Cost: ZMW {cost_breakdown['idle_cost_zmw']:,.2f}")
            print(f"  Total Cost: ZMW {cost_breakdown['total_cost_zmw']:,.2f}")
            print(f"  Net Profit: ZMW {cost_breakdown['net_profit_zmw']:,.2f}")
            print(f"  Currency: {cost_breakdown['currency']}")
            
            print(f"\n📋 Recommended Schedule:")
            for i, route in enumerate(data['evaluation']['recommended_schedule'], 1):
                print(f"  Day {i}: {route}")
        else:
            print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
