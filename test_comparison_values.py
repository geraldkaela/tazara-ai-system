#!/usr/bin/env python3
"""
Test Comparison Values - Check if API Returns Real Data
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_comparison_api():
    """Test the comparison API directly"""
    
    print('🧪 TESTING COMPARISON API VALUES')
    print('=' * 50)
    
    try:
        # Test the cost breakdown function directly
        from reinforcement_rl.improved_cost_model import get_improved_cost_breakdown
        
        print('✅ Testing cost breakdown function...')
        
        # Test with sample data
        breakdown = get_improved_cost_breakdown(
            cargo_delivered=1000,
            trains_used=5,
            delay_days=2,
            idle_days=3,
            active_trains=3,
            route_name="DAR_KAPIRI",
            cargo_type="Copper",
            customer_name="Default Customer"
        )
        
        print('📊 COST BREAKDOWN RESULTS:')
        print(f'   Revenue: ZMW {breakdown.get("revenue_zmw", 0):,.0f}')
        print(f'   Net Profit: ZMW {breakdown.get("net_profit_zmw", 0):,.0f}')
        print(f'   Total Cost: ZMW {breakdown.get("total_cost_zmw", 0):,.0f}')
        
        # Check if values are zero
        if breakdown.get("revenue_zmw", 0) == 0:
            print('❌ ISSUE: Revenue is zero!')
            return False
        else:
            print('✅ SUCCESS: Revenue has real value!')
        
        if breakdown.get("net_profit_zmw", 0) == 0:
            print('❌ ISSUE: Net profit is zero!')
            return False
        else:
            print('✅ SUCCESS: Net profit has real value!')
        
        print('\n🎯 COMPARISON SHOULD SHOW:')
        print(f'   Baseline Profit: ZMW {breakdown.get("net_profit_zmw", 0):,.0f}')
        print(f'   RL Profit: ZMW {breakdown.get("net_profit_zmw", 0):,.0f}+')
        print(f'   Revenue: ZMW {breakdown.get("revenue_zmw", 0):,.0f}')
        print(f'   Cargo Delivered: 1000 tons')
        
        return True
        
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')
        return False

if __name__ == "__main__":
    success = test_comparison_api()
    if success:
        print('\n🎉 COMPARISON API TEST PASSED!')
        print('The comparison tab should show real values!')
    else:
        print('\n❌ COMPARISON API TEST FAILED!')
        print('Check the cost breakdown function!')
