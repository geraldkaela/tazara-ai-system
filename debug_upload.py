#!/usr/bin/env python3
"""
Debug Upload Test - Check what the comparison API actually returns
"""

import requests
import json

def debug_upload():
    """Test the upload endpoint directly"""
    
    print('🔍 DEBUGGING COMPARISON UPLOAD')
    print('=' * 50)
    
    # Create test CSV content
    csv_content = """route,cargo
DAR_KAPIRI,500
DAR_MBEYA,300
KAPIRI_NDOLA,200"""
    
    # Test the upload endpoint
    url = "http://127.0.0.1:8000/compare/"
    
    try:
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        response = requests.post(url, files=files)
        
        print(f'📊 Response Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            
            print('✅ API Response Structure:')
            print(json.dumps(data, indent=2))
            
            # Check the specific values
            comparison = data.get('comparison', {})
            baseline = comparison.get('baseline_metrics', {})
            rl = comparison.get('rl_metrics', {})
            
            baseline_metrics = baseline.get('metrics', {})
            rl_metrics = rl.get('metrics', {})
            
            baseline_cost = baseline_metrics.get('cost_breakdown_zmw', {})
            rl_cost = rl_metrics.get('cost_breakdown_zmw', {})
            
            print('\n📈 KEY VALUES:')
            print(f'   Baseline Revenue: ZMW {baseline_cost.get("revenue_zmw", 0):,.0f}')
            print(f'   RL Revenue: ZMW {rl_cost.get("revenue_zmw", 0):,.0f}')
            print(f'   Baseline Profit: ZMW {baseline_cost.get("net_profit_zmw", 0):,.0f}')
            print(f'   RL Profit: ZMW {rl_cost.get("net_profit_zmw", 0):,.0f}')
            print(f'   Baseline Cargo: {baseline_metrics.get("total_cargo_delivered", 0)} tons')
            print(f'   RL Cargo: {rl_metrics.get("total_cargo_delivered", 0)} tons')
            
            # Check if values are zero
            if baseline_cost.get("revenue_zmw", 0) == 0:
                print('\n❌ ISSUE: API returning zero revenue!')
            else:
                print('\n✅ SUCCESS: API returning real values!')
                
        else:
            print(f'❌ ERROR: {response.status_code}')
            print(response.text)
            
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')

if __name__ == "__main__":
    debug_upload()
