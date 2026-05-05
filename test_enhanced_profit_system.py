#!/usr/bin/env python3
"""
Test the enhanced profit/loss system with real-world factors
"""

import sys
import os

# Add to project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_enhanced_profit_system():
    """Test the enhanced profit/loss calculations"""
    
    try:
        from reinforcement_rl.improved_cost_model import get_improved_cost_breakdown, dispatch_reward
        from reinforcement_rl.customer_contracts import get_customer_contract
        
        print('🧪 TESTING ENHANCED PROFIT/LOSS SYSTEM')
        print('=' * 50)
        
        # Test 1: Different cargo types
        print('\n📦 Test 1: Dynamic Cargo Pricing')
        copper_revenue = dispatch_reward(500, 'DAR_KAPIRI', 'Copper')
        coal_revenue = dispatch_reward(500, 'DAR_KAPIRI', 'Coal')
        container_revenue = dispatch_reward(500, 'DAR_KAPIRI', 'Containers')
        
        print(f'Copper (500 tons): ZMW {copper_revenue:,.0f}')
        print(f'Coal (500 tons): ZMW {coal_revenue:,.0f}')
        print(f'Containers (500 tons): ZMW {container_revenue:,.0f}')
        print(f'Copper vs Coal difference: ZMW {copper_revenue - coal_revenue:,.0f}')
        
        # Test 2: Customer contracts
        print('\n🏢 Test 2: Customer Contract Pricing')
        premium_customer = dispatch_reward(500, 'DAR_KAPIRI', 'Copper', 'Mining Corp Zambia')
        standard_customer = dispatch_reward(500, 'DAR_KAPIRI', 'Copper', 'Tanzania Export Ltd')
        bulk_customer = dispatch_reward(500, 'DAR_KAPIRI', 'Copper', 'Zambia Logistics')
        
        print(f'Mining Corp Zambia (Premium): ZMW {premium_customer:,.0f}')
        print(f'Tanzania Export Ltd (Standard): ZMW {standard_customer:,.0f}')
        print(f'Zambia Logistics (Bulk): ZMW {bulk_customer:,.0f}')
        print(f'Premium vs Bulk difference: ZMW {premium_customer - bulk_customer:,.0f}')
        
        # Test 3: Detailed cost breakdown
        print('\n📊 Test 3: Enhanced Cost Breakdown')
        breakdown = get_improved_cost_breakdown(
            cargo_delivered=800,
            trains_used=6,
            delay_days=0,
            idle_days=0,
            active_trains=6,
            route_name='DAR_KAPIRI',
            cargo_type='Copper',
            customer_name='Mining Corp Zambia'
        )
        
        print(f'Revenue: ZMW {breakdown["revenue_zmw"]:,.0f}')
        print(f'Total Cost: ZMW {breakdown["total_cost_zmw"]:,.0f}')
        print(f'Net Profit: ZMW {breakdown["net_profit_zmw"]:,.0f}')
        print(f'Profit Margin: {breakdown["profit_margin_percent"]:.1f}%')
        print(f'Fuel Cost: ZMW {breakdown["fuel_cost_zmw"]:,.0f}')
        print(f'Maintenance Cost: ZMW {breakdown["maintenance_cost_zmw"]:,.0f}')
        print(f'Staff Cost: ZMW {breakdown["staff_cost_zmw"]:,.0f}')
        print(f'Train Operating Cost: ZMW {breakdown["train_cost_zmw"]:,.0f}')
        
        # Test 4: Customer analysis
        if breakdown.get('customer_analysis'):
            customer = breakdown['customer_analysis']
            print(f'\n🎯 Customer Analysis:')
            print(f'Customer Rating: {customer.get("customer_rating", "N/A")}')
            print(f'Contract Tier: {customer.get("contract_tier", "N/A")}')
            print(f'Priority Score: {customer.get("priority_score", "N/A")}')
            print(f'Payment Terms: {customer.get("payment_terms_days", "N/A")} days')
        
        # Test 5: Route comparison
        print('\n🗺️ Test 5: Route Profitability Comparison')
        routes = ['DAR_KAPIRI', 'DAR_MBEYA', 'KAPIRI_NDOLA']
        
        for route in routes:
            route_breakdown = get_improved_cost_breakdown(
                cargo_delivered=500,
                trains_used=1,
                delay_days=0,
                idle_days=0,
                active_trains=1,
                route_name=route,
                cargo_type='Copper',
                customer_name='Mining Corp Zambia'
            )
            
            print(f'{route}:')
            print(f'  Revenue per ton: ZMW {route_breakdown["revenue_per_ton_zmw"]:,.0f}')
            print(f'  Cost per ton: ZMW {route_breakdown["cost_per_ton_zmw"]:,.0f}')
            print(f'  Profit per ton: ZMW {route_breakdown["revenue_per_ton_zmw"] - route_breakdown["cost_per_ton_zmw"]:,.0f}')
            print(f'  Margin: {route_breakdown["profit_margin_percent"]:.1f}%')
        
        print('\n✅ Enhanced Profit/Loss System Working!')
        return True
        
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        return False

if __name__ == "__main__":
    test_enhanced_profit_system()
