#!/usr/bin/env python3
"""
Debug Comparison API Response
"""

import sys
import os
import json

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_comparison_api():
    """Debug the comparison API response"""
    
    print('🔍 DEBUGGING COMPARISON API RESPONSE')
    print('=' * 50)
    
    try:
        # Import the compare function
        from api.routes.compare import compare_schedulers
        from fastapi import UploadFile
        from io import BytesIO
        
        print('✅ Successfully imported compare function')
        
        # Create a mock file
        csv_content = """route,cargo
DAR_KAPIRI,500
DAR_MBEYA,300
KAPIRI_NDOLA,200"""
        
        mock_file = UploadFile(filename="test.csv", file=BytesIO(csv_content.encode()))
        
        print('✅ Created mock CSV file')
        print(f'   Content: {csv_content}')
        
        # Call the compare function
        print('\n🚀 Calling compare_schedulers function...')
        result = compare_schedulers(mock_file)
        
        print('✅ Function executed successfully')
        
        # Check the result structure
        print('\n📊 API RESPONSE STRUCTURE:')
        print('=' * 40)
        
        print(f'   Filename: {result.get("filename", "N/A")}')
        print(f'   Routes detected: {result.get("routes_detected", 0)}')
        print(f'   Message: {result.get("message", "N/A")}')
        
        # Check comparison data
        comparison = result.get("comparison", {})
        print(f'\n📈 COMPARISON DATA:')
        print(f'   Has baseline_metrics: {"baseline_metrics" in comparison}')
        print(f'   Has rl_metrics: {"rl_metrics" in comparison}')
        print(f'   Has analysis: {"analysis" in comparison}')
        
        # Check baseline metrics
        baseline_metrics = comparison.get("baseline_metrics", {})
        baseline_data = baseline_metrics.get("metrics", {})
        baseline_cost = baseline_data.get("cost_breakdown_zmw", {})
        
        print(f'\n💰 BASELINE COST BREAKDOWN:')
        print(f'   Revenue: ZMW {baseline_cost.get("revenue_zmw", 0):,.0f}')
        print(f'   Net Profit: ZMW {baseline_cost.get("net_profit_zmw", 0):,.0f}')
        print(f'   Total Cost: ZMW {baseline_cost.get("total_cost_zmw", 0):,.0f}')
        
        # Check RL metrics
        rl_metrics = comparison.get("rl_metrics", {})
        rl_data = rl_metrics.get("metrics", {})
        rl_cost = rl_data.get("cost_breakdown_zmw", {})
        
        print(f'\n🤖 RL COST BREAKDOWN:')
        print(f'   Revenue: ZMW {rl_cost.get("revenue_zmw", 0):,.0f}')
        print(f'   Net Profit: ZMW {rl_cost.get("net_profit_zmw", 0):,.0f}')
        print(f'   Total Cost: ZMW {rl_cost.get("total_cost_zmw", 0):,.0f}')
        
        # Check if values are zero
        if baseline_cost.get("revenue_zmw", 0) == 0:
            print(f'\n❌ ISSUE: Baseline revenue is zero!')
        
        if rl_cost.get("revenue_zmw", 0) == 0:
            print(f'\n❌ ISSUE: RL revenue is zero!')
        
        # Print full response for debugging
        print(f'\n📄 FULL API RESPONSE:')
        print('=' * 40)
        print(json.dumps(result, indent=2, default=str))
        
        return True
        
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_comparison_api()
