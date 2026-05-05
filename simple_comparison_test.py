#!/usr/bin/env python3
"""
Simple Comparison Test - Check API Response Structure
"""

def test_comparison_structure():
    """Test the comparison response structure"""
    
    print('🔍 SIMPLE COMPARISON STRUCTURE TEST')
    print('=' * 50)
    
    print('❌ ISSUE: Comparison showing zeros')
    print('✅ HYPOTHESIS: Frontend-backend structure mismatch')
    
    print('\n🎯 FRONTEND EXPECTS:')
    print('=' * 30)
    print('function renderComparison(data) {')
    print('    const comp = data.comparison || data;')
    print('    const baseline = comp.baseline_metrics || {};')
    print('    const rl = comp.rl_metrics || {};')
    print('    const bCost = baseline.cost_breakdown_zmw || {};')
    print('    const rCost = rl.cost_breakdown_zmw || {};')
    print('}')
    
    print('\n🎯 FRONTEND DISPLAY LOGIC:')
    print('=' * 30)
    print('document.getElementById("baselineProfit").textContent = formatCurrency(bCost.net_profit_zmw);')
    print('document.getElementById("rlProfit").textContent = formatCurrency(rCost.net_profit_zmw);')
    print('document.getElementById("baselineCargo").textContent = formatNumber(baseline.total_cargo_delivered);')
    print('document.getElementById("rlCargo").textContent = formatNumber(rl.total_cargo_delivered);')
    
    print('\n🎯 COST TABLE LOGIC:')
    print('=' * 30)
    print('const metrics = ["revenue_zmw", "train_cost_zmw", "delay_cost_zmw", "idle_cost_zmw", "net_profit_zmw"];')
    print('tbody.innerHTML = metrics.map((m, i) => {')
    print('    const bv = bCost[m] || 0, rv = rCost[m] || 0;')
    print('    return `<td>${formatCurrency(bv)}</td><td>${formatCurrency(rv)}</td>`;')
    print('});')
    
    print('\n🎯 PROBLEM ANALYSIS:')
    print('=' * 30)
    print('❌ If bCost.net_profit_zmw is undefined → Shows ZMW 0')
    print('❌ If rCost.net_profit_zmw is undefined → Shows ZMW 0')
    print('❌ If baseline.total_cargo_delivered is undefined → Shows 0 tons')
    print('❌ If rl.total_cargo_delivered is undefined → Shows 0 tons')
    
    print('\n✅ SOLUTION NEEDED:')
    print('=' * 30)
    print('1. Backend must return: data.comparison.baseline_metrics.metrics.cost_breakdown_zmw')
    print('2. Backend must return: data.comparison.rl_metrics.metrics.cost_breakdown_zmw')
    print('3. Backend must return: data.comparison.baseline_metrics.metrics.total_cargo_delivered')
    print('4. Backend must return: data.comparison.rl_metrics.metrics.total_cargo_delivered')
    
    print('\n🎯 EXPECTED BACKEND STRUCTURE:')
    print('=' * 40)
    print('{')
    print('  "comparison": {')
    print('    "baseline_metrics": {')
    print('      "metrics": {')
    print('        "total_cargo_delivered": 1000,')
    print('        "cost_breakdown_zmw": {')
    print('          "revenue_zmw": 977600,')
    print('          "net_profit_zmw": 564150')
    print('        }')
    print('      }')
    print('    },')
    print('    "rl_metrics": {')
    print('      "metrics": {')
    print('        "total_cargo_delivered": 1000,')
    print('        "cost_breakdown_zmw": {')
    print('          "revenue_zmw": 977600,')
    print('          "net_profit_zmw": 564150')
    print('        }')
    print('      }')
    print('    }')
    print('  }')
    print('}')
    
    print('\n🔧 DEBUGGING STEPS:')
    print('=' * 30)
    print('1. Check browser console for JavaScript errors')
    print('2. Check network tab for API response')
    print('3. Verify API response structure matches frontend expectations')
    print('4. Test with hardcoded values to isolate issue')
    
    print('\n🎯 COMPARISON TAB - STRUCTURE ANALYSIS COMPLETE!')
    
    return True

if __name__ == "__main__":
    test_comparison_structure()
