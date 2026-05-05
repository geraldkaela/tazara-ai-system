#!/usr/bin/env python3
"""
Test Cost Breakdown Function
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_cost_breakdown():
    """Test the cost breakdown function"""
    
    try:
        from reinforcement_rl.improved_cost_model import get_improved_cost_breakdown
        
        print('🧪 TESTING COST BREAKDOWN FUNCTION')
        print('=' * 50)
        
        # Test with sample data
        cargo_delivered = 1000
        trains_used = 5
        delay_days = 2
        idle_days = 3
        active_trains = 3
        route_name = "DAR_KAPIRI"
        cargo_type = "Copper"
        customer_name = "Default Customer"
        
        print(f'📊 Test Parameters:')
        print(f'   Cargo Delivered: {cargo_delivered} tons')
        print(f'   Trains Used: {trains_used}')
        print(f'   Delay Days: {delay_days}')
        print(f'   Idle Days: {idle_days}')
        print(f'   Route: {route_name}')
        print(f'   Cargo Type: {cargo_type}')
        print(f'   Customer: {customer_name}')
        
        # Calculate cost breakdown
        breakdown = get_improved_cost_breakdown(
            cargo_delivered=cargo_delivered,
            trains_used=trains_used,
            delay_days=delay_days,
            idle_days=idle_days,
            active_trains=active_trains,
            route_name=route_name,
            cargo_type=cargo_type,
            customer_name=customer_name
        )
        
        print(f'\n💰 COST BREAKDOWN RESULTS:')
        print('=' * 40)
        
        print(f'   Revenue: ZMW {breakdown.get("revenue_zmw", 0):,.0f}')
        print(f'   Train Cost: ZMW {breakdown.get("train_cost_zmw", 0):,.0f}')
        print(f'   Staff Cost: ZMW {breakdown.get("staff_cost_zmw", 0):,.0f}')
        print(f'   Delay Cost: ZMW {breakdown.get("delay_cost_zmw", 0):,.0f}')
        print(f'   Idle Cost: ZMW {breakdown.get("idle_cost_zmw", 0):,.0f}')
        print(f'   Fuel Cost: ZMW {breakdown.get("fuel_cost_zmw", 0):,.0f}')
        print(f'   Maintenance Cost: ZMW {breakdown.get("maintenance_cost_zmw", 0):,.0f}')
        print(f'   Total Cost: ZMW {breakdown.get("total_cost_zmw", 0):,.0f}')
        print(f'   Net Profit: ZMW {breakdown.get("net_profit_zmw", 0):,.0f}')
        print(f'   Profit Margin: {breakdown.get("profit_margin_percent", 0):.1f}%')
        
        # Check if values are zero
        if breakdown.get("revenue_zmw", 0) == 0:
            print(f'\n❌ ISSUE: Revenue is zero!')
            print(f'   This suggests the cost breakdown function has issues')
        
        if breakdown.get("net_profit_zmw", 0) == 0:
            print(f'\n❌ ISSUE: Net profit is zero!')
            print(f'   This suggests the cost breakdown function has issues')
        
        print(f'\n✅ COST BREAKDOWN TEST COMPLETE')
        return True
        
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')
        return False

if __name__ == "__main__":
    test_cost_breakdown()
