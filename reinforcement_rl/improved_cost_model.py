"""
Improved Cost Model for Multi-Route TAZARA System
Balanced rewards that encourage cargo movement with real-world pricing and customer contracts
"""

# 🚆 Dynamic Cargo Pricing (ZMW per ton) - Based on realistic market values
CARGO_PRICING = {
    "Copper": 1200,     # High-value mineral cargo (increased from 800)
    "Coal": 600,        # Bulk commodity cargo (increased from 400)
    "Containers": 900,  # Mixed commercial cargo (increased from 600)
    "Fuel": 1000,       # Hazardous cargo premium (increased from 700)
    "Other": 750        # Standard cargo rate (increased from 500)
}

# 🚆 Default pricing for unknown cargo types
DEFAULT_CARGO_PRICE = 750

# 🚆 Route-specific distance multipliers (based on actual distances)
ROUTE_DISTANCE_MULTIPLIER = {
    "DAR_KAPIRI": 1.2,  # 1,860 km - long route premium
    "DAR_MBEYA": 1.0,   # 1,040 km - standard rate
    "MBEYA_KASAMA": 1.1, # 1,340 km - medium-long route
    "KAPIRI_NDOLA": 0.8, # 290 km - short route discount
    "DAR_KIDATU": 0.9,  # 450 km - short-medium route
    "KIDATU_TRANS_SHIPMENT": 1.0  # Trans-shipment - standard rate
}

# 🚆 Route-specific operational bonuses (adjusted for distance)
ROUTE_EFFICIENCY_BONUS = {
    "DAR_KAPIRI": 8000,    # Increased for long route
    "DAR_MBEYA": 4000,     # Medium route bonus
    "MBEYA_KASAMA": 6000,  # Medium-long route
    "KAPIRI_NDOLA": 1500,  # Short route bonus
    "DAR_KIDATU": 2000,    # Short-medium route
    "KIDATU_TRANS_SHIPMENT": 2500  # Trans-shipment bonus
}

# 🚆 Operating costs (updated for realism)
TRAIN_OPERATING_COST_PER_DAY = 5000  # Increased operating cost (from 3000)
DELAY_COST_PER_DAY = 15000           # Higher delay cost (from 12000)
IDLE_COST_PER_DAY = 200             # Slightly higher idle cost (from 150)
MAINTENANCE_COST_PER_KM = 30         # ZMW per km per train (from 25)
FUEL_COST_PER_LITER = 30             # ZMW per liter (from 25)
FUEL_CONSUMPTION_PER_KM = 4.0        # Liters per km per train (from 3.5)
STAFF_COST_PER_TRAIN_PER_DAY = 1200  # ZMW per train per day (from 800)

# 🚆 Route distances (in km) for fuel/maintenance calculations
ROUTE_DISTANCES = {
    "DAR_KAPIRI": 1860,      # Dar es Salaam to Kapiri Mposhi
    "DAR_MBEYA": 1040,       # Dar es Salaam to Mbeya
    "MBEYA_KASAMA": 1340,    # Mbeya to Kasama
    "KAPIRI_NDOLA": 290,     # Kapiri Mposhi to Ndola
    "DAR_KIDATU": 450,       # Dar es Salaam to Kidatu
    "KIDATU_TRANS_SHIPMENT": 0  # Trans-shipment (no distance)
}

# Import customer contracts for dynamic pricing
try:
    from .customer_contracts import calculate_customer_pricing, get_customer_contract
    CUSTOMER_CONTRACTS_AVAILABLE = True
except ImportError:
    CUSTOMER_CONTRACTS_AVAILABLE = False
    def calculate_customer_pricing(base_price, customer_name, cargo_volume, cargo_type, route_name):
        return base_price  # Fallback to base pricing

# 🚆 Multi-train coordination bonus
COORDINATION_BONUS = {
    1: 0,      # 1 train active
    2: 1000,    # 2 trains coordinating
    3: 2000,    # 3 trains coordinating
    4: 3000,    # 4 trains coordinating
    5: 4000,    # 5 trains coordinating
    6: 5000,    # 6 trains coordinating
}

def dispatch_reward(cargo_delivered, route_name, cargo_type="Other", customer_name=None):
    """
    Enhanced revenue calculation with dynamic pricing, distance factors, and customer contracts
    """
    # Get base price for cargo type
    base_price_per_ton = CARGO_PRICING.get(cargo_type, DEFAULT_CARGO_PRICE)
    
    # Apply route distance multiplier
    distance_multiplier = ROUTE_DISTANCE_MULTIPLIER.get(route_name, 1.0)
    adjusted_price_per_ton = base_price_per_ton * distance_multiplier
    
    # Apply customer-specific pricing if available
    if customer_name and CUSTOMER_CONTRACTS_AVAILABLE:
        final_price_per_ton = calculate_customer_pricing(
            adjusted_price_per_ton, 
            customer_name, 
            cargo_delivered, 
            cargo_type, 
            route_name
        )
    else:
        final_price_per_ton = adjusted_price_per_ton
    
    # Calculate base revenue
    base_revenue = cargo_delivered * final_price_per_ton
    
    # Add route-specific bonus
    route_bonus = ROUTE_EFFICIENCY_BONUS.get(route_name, 0)
    
    return base_revenue + route_bonus

def calculate_fuel_cost(route_name, cargo_weight=0):
    """
    Calculate fuel cost based on route distance and cargo weight
    """
    distance = ROUTE_DISTANCES.get(route_name, 0)
    if distance == 0:
        return 0
    
    # Base fuel consumption
    fuel_consumed = distance * FUEL_CONSUMPTION_PER_KM
    
    # Increase consumption for heavier cargo (every 100 tons adds 10% consumption)
    if cargo_weight > 0:
        cargo_factor = 1 + (cargo_weight / 1000)  # Max 2x consumption for very heavy loads
        fuel_consumed *= cargo_factor
    
    return fuel_consumed * FUEL_COST_PER_LITER

def calculate_maintenance_cost(route_name):
    """
    Calculate maintenance cost based on route distance
    """
    distance = ROUTE_DISTANCES.get(route_name, 0)
    return distance * MAINTENANCE_COST_PER_KM

def train_usage_penalty(trains_used):
    """
    Reduced operating cost in ZMW for using trains
    """
    return trains_used * TRAIN_OPERATING_COST_PER_DAY

def delay_penalty(delay_days):
    """
    Reduced delay cost in ZMW
    """
    return delay_days * DELAY_COST_PER_DAY

def idle_penalty(idle_days, active_trains=0):
    """
    Strong penalty for idling to discourage this behavior
    """
    base_idle_cost = idle_days * IDLE_COST_PER_DAY
    
    # Make penalty much stronger when no trains are active
    if active_trains == 0:
        # All trains idle - maximum penalty
        return base_idle_cost * 2  # Double penalty for complete inactivity
    elif active_trains < 3:
        # Very few trains active - strong penalty
        return base_idle_cost * 1.5
    else:
        # Some trains active - moderate penalty
        return base_idle_cost

def coordination_bonus(active_trains, total_trains):
    """
    Bonus for coordinating multiple trains effectively
    """
    return COORDINATION_BONUS.get(active_trains, 0)

def get_improved_cost_breakdown(
    cargo_delivered,
    trains_used,
    delay_days,
    idle_days,
    active_trains=0,
    route_name="DAR_KAPIRI",
    cargo_type="Other",
    customer_name=None
):
    """
    Enhanced cost breakdown with realistic business factors and customer contracts
    """
    # Calculate revenue with dynamic pricing
    revenue = dispatch_reward(cargo_delivered, route_name, cargo_type, customer_name)
    
    # Calculate detailed costs
    train_cost = trains_used * TRAIN_OPERATING_COST_PER_DAY
    staff_cost = trains_used * STAFF_COST_PER_TRAIN_PER_DAY
    delay_cost = delay_days * DELAY_COST_PER_DAY
    idle_cost = idle_penalty(idle_days, active_trains)
    
    # Calculate route-specific costs
    fuel_cost = calculate_fuel_cost(route_name, cargo_delivered)
    maintenance_cost = calculate_maintenance_cost(route_name)
    
    # Add coordination bonus
    bonus = coordination_bonus(active_trains, trains_used)
    
    # Total costs
    operational_costs = train_cost + staff_cost + delay_cost + idle_cost
    route_costs = fuel_cost + maintenance_cost
    total_cost = operational_costs + route_costs
    
    # Net profit
    net_profit = revenue + bonus - total_cost
    
    # Customer contract analysis
    customer_info = {}
    if customer_name and CUSTOMER_CONTRACTS_AVAILABLE:
        try:
            from .customer_contracts import analyze_customer_profitability
            customer_info = analyze_customer_profitability(customer_name, revenue, total_cost, cargo_delivered)
        except ImportError:
            customer_info = {"customer_name": customer_name, "contract_tier": "Unknown"}
    
    return {
        "revenue_zmw": revenue,
        "train_cost_zmw": train_cost,
        "staff_cost_zmw": staff_cost,
        "delay_cost_zmw": delay_cost,
        "idle_cost_zmw": idle_cost,
        "fuel_cost_zmw": fuel_cost,
        "maintenance_cost_zmw": maintenance_cost,
        "coordination_bonus_zmw": bonus,
        "operational_costs_zmw": operational_costs,
        "route_costs_zmw": route_costs,
        "total_cost_zmw": total_cost,
        "net_profit_zmw": net_profit,
        "currency": "ZMW",
        "cargo_type": cargo_type,
        "route_name": route_name,
        "customer_name": customer_name,
        "efficiency_score": min(100, (cargo_delivered / max(trains_used * 7, 1)) * 10),  # 7 days typical schedule
        "profit_margin_percent": (net_profit / revenue * 100) if revenue > 0 else 0,
        "cost_per_ton_zmw": (total_cost / cargo_delivered) if cargo_delivered > 0 else 0,
        "revenue_per_ton_zmw": (revenue / cargo_delivered) if cargo_delivered > 0 else 0,
        "customer_analysis": customer_info
    }
