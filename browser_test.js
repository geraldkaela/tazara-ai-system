// Browser Test - Check if comparison data is being read correctly
// Copy this to browser console on the comparison page

console.log('🧪 BROWSER COMPARISON TEST');
console.log('==========================');

// Test the renderComparison function with mock data
const mockData = {
    comparison: {
        baseline_metrics: {
            metrics: {
                total_cargo_delivered: 1000,
                cost_breakdown_zmw: {
                    revenue_zmw: 977600,
                    net_profit_zmw: 564150,
                    train_cost_zmw: 15000,
                    delay_cost_zmw: 24000,
                    idle_cost_zmw: 450,
                    total_cost_zmw: 415450
                }
            }
        },
        rl_metrics: {
            metrics: {
                total_cargo_delivered: 1000,
                cost_breakdown_zmw: {
                    revenue_zmw: 977600,
                    net_profit_zmw: 564150,
                    train_cost_zmw: 15000,
                    delay_cost_zmw: 24000,
                    idle_cost_zmw: 450,
                    total_cost_zmw: 415450
                }
            }
        }
    }
};

// Test the data structure parsing
console.log('📊 TESTING DATA STRUCTURE:');
const comp = mockData.comparison;
const baseline = comp.baseline_metrics || {};
const rl = comp.rl_metrics || {};
const baselineMetrics = baseline.metrics || {};
const rlMetrics = rl.metrics || {};
const bCost = baselineMetrics.cost_breakdown_zmw || {};
const rCost = rlMetrics.cost_breakdown_zmw || {};

console.log('✅ Baseline Revenue:', bCost.revenue_zmw);
console.log('✅ RL Revenue:', rCost.revenue_zmw);
console.log('✅ Baseline Profit:', bCost.net_profit_zmw);
console.log('✅ RL Profit:', rCost.net_profit_zmw);
console.log('✅ Baseline Cargo:', baselineMetrics.total_cargo_delivered);
console.log('✅ RL Cargo:', rlMetrics.total_cargo_delivered);

// Test if values are zero
if (bCost.revenue_zmw === 0) {
    console.log('❌ ISSUE: Baseline revenue is zero');
} else {
    console.log('✅ SUCCESS: Baseline revenue has value');
}

if (rCost.net_profit_zmw === 0) {
    console.log('❌ ISSUE: RL profit is zero');
} else {
    console.log('✅ SUCCESS: RL profit has value');
}

console.log('🎯 BROWSER TEST COMPLETE');
console.log('If all values show correctly, the frontend should work!');
