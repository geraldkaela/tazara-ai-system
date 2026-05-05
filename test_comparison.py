import requests

url = "http://127.0.0.1:8000/compare/"
file_path = "uploads/testAI.xlsx"

try:
    with open(file_path, "rb") as f:
        files = {"file": ("testAI.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        headers = {"accept": "application/json"}
        
        response = requests.post(url, files=files, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            comparison = data["comparison"]
            
            print(f"\n🔄 Baseline vs RL Comparison Results:")
            print(f"Routes detected: {data['routes_detected']}")
            
            baseline = comparison["baseline"]["metrics"]
            rl = comparison["rl"]["metrics"]
            analysis = comparison["analysis"]
            
            print(f"\n📊 Financial Comparison:")
            print(f"Baseline Net Profit: ZMW {baseline['cost_breakdown_zmw']['net_profit_zmw']:,.2f}")
            print(f"RL Net Profit: ZMW {rl['cost_breakdown_zmw']['net_profit_zmw']:,.2f}")
            print(f"Profit Improvement: ZMW {analysis['profit_improvement_zmw']:,.2f}")
            
            print(f"\n📦 Cargo Comparison:")
            print(f"Baseline Cargo: {baseline['total_cargo_delivered']:,.0f} tons")
            print(f"RL Cargo: {rl['total_cargo_delivered']:,.0f} tons")
            print(f"Cargo Improvement: {analysis['cargo_efficiency_improvement']:,.0f} tons")
            
            print(f"\n📋 Schedule Comparison:")
            print(f"Baseline Schedule: {comparison['baseline']['schedule']}")
            print(f"RL Schedule: {comparison['rl']['schedule']}")
            
        else:
            print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
