"""
Phase 1 – Step 3
Real cost model for cargo operations in Zambian Kwacha (ZMW)
"""

# ZMW conversion factors
CARGO_REVENUE_PER_TON = 50  # ZMW per ton of cargo delivered
TRAIN_OPERATING_COST_PER_DAY = 5000  # ZMW per train per day
DELAY_COST_PER_DAY = 15000  # ZMW for delaying operations
IDLE_COST_PER_DAY = 20000  # ZMW for idle operations

def dispatch_reward(cargo_delivered):
    """
    Revenue in ZMW for successfully delivering cargo
    """
    return cargo_delivered * CARGO_REVENUE_PER_TON


def train_usage_penalty(trains_used):
    """
    Operating cost in ZMW for using trains
    """
    return trains_used * TRAIN_OPERATING_COST_PER_DAY


def delay_penalty():
    """
    Cost in ZMW for delaying operations
    """
    return DELAY_COST_PER_DAY


def idle_penalty():
    """
    Cost in ZMW for skipping operations
    """
    return IDLE_COST_PER_DAY


def get_cost_breakdown(cargo_delivered, trains_used, delay_days=0, idle_days=0):
    """
    Returns detailed cost breakdown in ZMW
    """
    revenue = dispatch_reward(cargo_delivered)
    train_cost = train_usage_penalty(trains_used)
    delay_cost = delay_penalty() * delay_days
    idle_cost = idle_penalty() * idle_days
    
    total_cost = train_cost + delay_cost + idle_cost
    net_profit = revenue - total_cost
    
    return {
        "revenue_zmw": revenue,
        "train_cost_zmw": train_cost,
        "delay_cost_zmw": delay_cost,
        "idle_cost_zmw": idle_cost,
        "total_cost_zmw": total_cost,
        "net_profit_zmw": net_profit,
        "currency": "ZMW"
    }
