from reinforcement_rl.baseline_scheduler import BaselineScheduler

# Test baseline scheduler
scheduler = BaselineScheduler(num_trains=5, max_days=7)

# Test with sample cargo data
initial_cargo = {
    "DAR_KAPIRI": 500,
    "DAR_MBEYA": 320, 
    "KAPIRI_NDOLA": 120
}

print("🔄 Testing Baseline Scheduler")
print("=" * 40)
print(f"Initial Cargo: {initial_cargo}")

schedule, metrics = scheduler.simulate_week(initial_cargo)

print(f"\n📋 Schedule: {schedule}")
print(f"\n📊 Metrics:")
print(f"  Total Cargo Delivered: {metrics['total_cargo_delivered']} tons")
print(f"  Trains Used: {metrics['trains_used']}")
print(f"  Delay Days: {metrics['delay_days']}")
print(f"  Idle Days: {metrics['idle_days']}")

cost_breakdown = metrics['cost_breakdown_zmw']
print(f"\n💰 ZMW Cost Breakdown:")
print(f"  Revenue: ZMW {cost_breakdown['revenue_zmw']:,.2f}")
print(f"  Train Cost: ZMW {cost_breakdown['train_cost_zmw']:,.2f}")
print(f"  Delay Cost: ZMW {cost_breakdown['delay_cost_zmw']:,.2f}")
print(f"  Idle Cost: ZMW {cost_breakdown['idle_cost_zmw']:,.2f}")
print(f"  Net Profit: ZMW {cost_breakdown['net_profit_zmw']:,.2f}")
print(f"  Currency: {cost_breakdown['currency']}")
