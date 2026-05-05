"""
Customer Contracts System for TAZARA Railway
Manages pricing tiers, margins, and customer-specific agreements
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ContractTier(Enum):
    PREMIUM = "premium"      # High-margin contracts
    STANDARD = "standard"    # Standard pricing
    BULK = "bulk"           # Volume discounts
    GOVERNMENT = "government"  # Government contracts

@dataclass
class CustomerContract:
    """Customer contract with specific pricing and terms"""
    customer_name: str
    contract_tier: ContractTier
    margin_multiplier: float  # Multiplier for base pricing
    volume_discount: float    # Discount for high volume (0-1)
    priority_bonus: int       # Priority in scheduling (1-5)
    payment_terms: int        # Days to payment
    cargo_preferences: List[str]  # Preferred cargo types
    route_preferences: List[str]  # Preferred routes

# Customer contract database
CUSTOMER_CONTRACTS = {
    "Mining Corp Zambia": CustomerContract(
        customer_name="Mining Corp Zambia",
        contract_tier=ContractTier.PREMIUM,
        margin_multiplier=1.15,  # 15% premium
        volume_discount=0.05,    # 5% discount for volume
        priority_bonus=5,        # Highest priority
        payment_terms=30,         # 30 days payment
        cargo_preferences=["Copper", "Containers"],
        route_preferences=["DAR_KAPIRI", "KAPIRI_NDOLA"]
    ),
    
    "Tanzania Export Ltd": CustomerContract(
        customer_name="Tanzania Export Ltd",
        contract_tier=ContractTier.STANDARD,
        margin_multiplier=1.0,   # Standard pricing
        volume_discount=0.02,    # 2% volume discount
        priority_bonus=3,        # Medium priority
        payment_terms=45,         # 45 days payment
        cargo_preferences=["Containers", "Other"],
        route_preferences=["DAR_MBEYA", "DAR_KAPIRI"]
    ),
    
    "Zambia Logistics": CustomerContract(
        customer_name="Zambia Logistics",
        contract_tier=ContractTier.BULK,
        margin_multiplier=0.9,    # 10% discount
        volume_discount=0.10,    # 10% volume discount
        priority_bonus=2,        # Low priority
        payment_terms=60,         # 60 days payment
        cargo_preferences=["Fuel", "Coal"],
        route_preferences=["KAPIRI_NDOLA", "MBEYA_KASAMA"]
    ),
    
    "Government Transport": CustomerContract(
        customer_name="Government Transport",
        contract_tier=ContractTier.GOVERNMENT,
        margin_multiplier=0.85,   # 15% government discount
        volume_discount=0.15,    # 15% volume discount
        priority_bonus=4,        # High priority
        payment_terms=90,         # 90 days payment
        cargo_preferences=["Other", "Containers"],
        route_preferences=["DAR_MBEYA", "DAR_KAPIRI"]
    )
}

# Default contract for unknown customers
DEFAULT_CONTRACT = CustomerContract(
    customer_name="Default Customer",
    contract_tier=ContractTier.STANDARD,
    margin_multiplier=1.0,
    volume_discount=0.0,
    priority_bonus=3,
    payment_terms=45,
    cargo_preferences=["Other"],
    route_preferences=["DAR_KAPIRI", "DAR_MBEYA"]
)

def get_customer_contract(customer_name: str) -> CustomerContract:
    """Get customer contract by name"""
    return CUSTOMER_CONTRACTS.get(customer_name, DEFAULT_CONTRACT)

def calculate_customer_pricing(
    base_price: float,
    customer_name: str,
    cargo_volume: float,
    cargo_type: str,
    route_name: str
) -> float:
    """Calculate customer-specific pricing"""
    contract = get_customer_contract(customer_name)
    
    # Apply margin multiplier
    adjusted_price = base_price * contract.margin_multiplier
    
    # Apply volume discount if threshold met
    volume_threshold = 1000  # 1000 tons for volume discount
    if cargo_volume >= volume_threshold:
        adjusted_price *= (1 - contract.volume_discount)
    
    # Apply cargo preference bonus
    if cargo_type in contract.cargo_preferences:
        adjusted_price *= 1.02  # 2% bonus for preferred cargo
    
    # Apply route preference bonus
    if route_name in contract.route_preferences:
        adjusted_price *= 1.01  # 1% bonus for preferred routes
    
    return adjusted_price

def get_customer_priority_score(customer_name: str) -> int:
    """Get customer scheduling priority"""
    contract = get_customer_contract(customer_name)
    return contract.priority_bonus

def analyze_customer_profitability(
    customer_name: str,
    revenue: float,
    costs: float,
    cargo_volume: float
) -> Dict:
    """Analyze customer profitability metrics"""
    contract = get_customer_contract(customer_name)
    
    profit = revenue - costs
    profit_margin = (profit / revenue) if revenue > 0 else 0
    profit_per_ton = profit / cargo_volume if cargo_volume > 0 else 0
    
    # Calculate customer lifetime value (simplified)
    payment_delay_cost = contract.payment_terms * 0.01 * revenue  # 1% per day cost of capital
    
    return {
        "customer_name": customer_name,
        "contract_tier": contract.contract_tier.value,
        "revenue_zmw": revenue,
        "costs_zmw": costs,
        "profit_zmw": profit,
        "profit_margin_percent": profit_margin * 100,
        "profit_per_ton_zmw": profit_per_ton,
        "cargo_volume_tons": cargo_volume,
        "payment_terms_days": contract.payment_terms,
        "payment_delay_cost_zmw": payment_delay_cost,
        "net_profit_after_payment_cost": profit - payment_delay_cost,
        "priority_score": contract.priority_bonus,
        "customer_rating": "Excellent" if profit_margin > 0.25 else "Good" if profit_margin > 0.15 else "Fair" if profit_margin > 0.05 else "Poor"
    }

def get_most_profitable_routes(customer_name: str = None) -> List[Dict]:
    """Analyze most profitable routes for a customer or overall"""
    from .improved_cost_model import CARGO_PRICING, ROUTE_DISTANCES
    
    routes = ["DAR_KAPIRI", "DAR_MBEYA", "MBEYA_KASAMA", "KAPIRI_NDOLA", "DAR_KIDATU", "KIDATU_TRANS_SHIPMENT"]
    profitability = []
    
    for route in routes:
        # Sample cargo type for analysis
        sample_cargo = "Copper" if "KAPIRI" in route else "Containers"
        base_price = CARGO_PRICING.get(sample_cargo, 500)
        
        # Calculate sample pricing
        if customer_name:
            price = calculate_customer_pricing(base_price, customer_name, 1000, sample_cargo, route)
        else:
            price = base_price
        
        # Estimate costs
        distance = ROUTE_DISTANCES.get(route, 0)
        fuel_cost = distance * 25 * 3.5  # Rough fuel cost estimate
        maintenance_cost = distance * 25
        operating_cost = 3000  # Daily cost
        
        total_cost = fuel_cost + maintenance_cost + operating_cost
        profit = price - total_cost
        margin = (profit / price) if price > 0 else 0
        
        profitability.append({
            "route_name": route,
            "cargo_type": sample_cargo,
            "revenue_per_ton": price,
            "estimated_cost_per_ton": total_cost / 1000 if distance > 0 else operating_cost / 1000,
            "profit_per_ton": profit / 1000 if distance > 0 else (price - operating_cost) / 1000,
            "profit_margin_percent": margin * 100,
            "distance_km": distance,
            "customer_specific": customer_name is not None
        })
    
    # Sort by profit margin
    return sorted(profitability, key=lambda x: x["profit_margin_percent"], reverse=True)
