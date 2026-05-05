from reinforcement_rl.cost_model import get_cost_breakdown

# Test the ZMW cost model
test_cases = [
    {"cargo": 1000, "trains": 2, "delays": 1, "idle": 0},
    {"cargo": 500, "trains": 1, "delays": 0, "idle": 2},
    {"cargo": 2000, "trains": 3, "delays": 0, "idle": 0}
]

print("🇿🇲 ZMW Cost Model Test Results")
print("=" * 50)

for i, case in enumerate(test_cases, 1):
    result = get_cost_breakdown(
        cargo_delivered=case["cargo"],
        trains_used=case["trains"],
        delay_days=case["delays"],
        idle_days=case["idle"]
    )
    
    print(f"\nTest Case {i}:")
    print(f"  Cargo: {case['cargo']} tons")
    print(f"  Trains: {case['trains']}")
    print(f"  Delays: {case['delays']} days")
    print(f"  Idle: {case['idle']} days")
    print(f"  Revenue: ZMW {result['revenue_zmw']:,.2f}")
    print(f"  Train Cost: ZMW {result['train_cost_zmw']:,.2f}")
    print(f"  Delay Cost: ZMW {result['delay_cost_zmw']:,.2f}")
    print(f"  Idle Cost: ZMW {result['idle_cost_zmw']:,.2f}")
    print(f"  Total Cost: ZMW {result['total_cost_zmw']:,.2f}")
    print(f"  Net Profit: ZMW {result['net_profit_zmw']:,.2f}")
