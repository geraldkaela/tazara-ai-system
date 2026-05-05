"""Schedule fragility and what-if analysis for cargo demand scenarios.

Analyzes scheduling resilience and simulates alternative demand scenarios.
Supports:
- Schedule fragility scoring (how vulnerable to disruptions)
- Bottleneck impact assessment
- What-if scenario modeling (demand shocks, seasonal variations)
- Capacity utilization forecasts

Usage:
    python -m analytics.schedule_fragility
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple
import json

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


FEATURES_PATH = Path("data/processed/features.csv")
RISK_REPORT_PATH = Path("metrics/risk_analysis.json")
FRAGILITY_REPORT_PATH = Path("metrics/schedule_fragility.json")


def compute_slack_time(demand: float, capacity: float) -> float:
    """
    Compute slack time (buffer) as a percentage.
    Slack = (Capacity - Demand) / Capacity * 100
    Negative slack indicates over-capacity.
    """
    if capacity <= 0:
        return 0.0
    return (capacity - demand) / capacity * 100


def compute_fragility_score(
    demand: float,
    volatility: float,
    capacity: float,
    mean_demand: float,
    std_demand: float
) -> float:
    """
    Compute schedule fragility score (0-100).
    Higher score = more fragile (more prone to disruptions).
    """
    score = 0.0
    
    # Capacity utilization risk (0-40)
    util_ratio = demand / capacity if capacity > 0 else 1.0
    if util_ratio > 0.9:
        score += 40  # Critical utilization
    elif util_ratio > 0.75:
        score += 30
    elif util_ratio > 0.6:
        score += 15
    else:
        score += 5
    
    # Volatility risk (0-30): unpredictable demand = fragile schedule
    vol_score = min(30, volatility * 5)
    score += vol_score
    
    # Demand spike risk (0-30): proximity to capacity
    normalized_demand = (demand - mean_demand) / max(std_demand, 1.0)
    if normalized_demand > 1.5:
        score += 30  # Demand spike
    elif normalized_demand > 0.5:
        score += 15
    else:
        score += 5
    
    return min(100, score)


def classify_fragility(score: float) -> str:
    """Classify fragility level."""
    if score < 25:
        return "robust"
    elif score < 50:
        return "flexible"
    elif score < 75:
        return "fragile"
    else:
        return "critical"


def simulate_demand_shock(
    df: pd.DataFrame,
    shock_type: str = "surge",
    shock_magnitude: float = 0.2
) -> pd.DataFrame:
    """
    Simulate demand shock scenarios.
    
    Args:
        df: Original demand dataframe
        shock_type: 'surge' (increase), 'drop' (decrease), 'volatility' (increase uncertainty)
        shock_magnitude: Magnitude of shock (0.2 = 20% change)
    
    Returns:
        DataFrame with shocked demand values
    """
    df_shock = df.copy()
    
    if shock_type == "surge":
        # Increase demand uniformly
        df_shock["cargo_tons"] = df_shock["cargo_tons"] * (1 + shock_magnitude)
    elif shock_type == "drop":
        # Decrease demand uniformly
        df_shock["cargo_tons"] = df_shock["cargo_tons"] * (1 - shock_magnitude)
    elif shock_type == "volatility":
        # Add random noise proportional to shock_magnitude
        noise = np.random.normal(0, df_shock["cargo_tons"].std() * shock_magnitude, len(df_shock))
        df_shock["cargo_tons"] = np.maximum(0, df_shock["cargo_tons"] + noise)
    
    return df_shock


def analyze_capacity_utilization(
    df: pd.DataFrame,
    nominal_capacity: float = 200.0
) -> Dict:
    """Analyze capacity utilization patterns."""
    demand = df["cargo_tons"].values
    utilization = demand / nominal_capacity * 100
    
    return {
        "nominal_capacity": float(nominal_capacity),
        "mean_utilization": float(utilization.mean()),
        "max_utilization": float(utilization.max()),
        "min_utilization": float(utilization.min()),
        "days_over_90_pct": int((utilization > 90).sum()),
        "days_over_80_pct": int((utilization > 80).sum()),
        "days_over_70_pct": int((utilization > 70).sum()),
    }


def run_schedule_fragility_analysis() -> None:
    """Run schedule fragility and what-if analysis."""
    logger.info("Starting schedule fragility and what-if analysis...")
    
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Features file not found: {FEATURES_PATH}")
    
    df = pd.read_csv(FEATURES_PATH, parse_dates=["date"])
    logger.info(f"Loaded {len(df)} records for fragility analysis")
    
    # Load risk data if available
    risk_data = None
    if RISK_REPORT_PATH.exists():
        with open(RISK_REPORT_PATH) as f:
            risk_data = json.load(f)
    
    # Compute fragility metrics
    demand = df["cargo_tons"].values
    mean_demand = demand.mean()
    std_demand = demand.std()
    
    # Simple volatility estimate
    volatility = df["cargo_tons"].rolling(7).std().fillna(0).values
    
    nominal_capacity = 200.0
    
    # Compute per-day fragility scores
    fragility_scores = []
    for i in range(len(df)):
        score = compute_fragility_score(
            demand[i],
            volatility[i],
            nominal_capacity,
            mean_demand,
            std_demand
        )
        level = classify_fragility(score)
        slack = compute_slack_time(demand[i], nominal_capacity)
        
        fragility_scores.append({
            "date": df.iloc[i]["date"].strftime("%Y-%m-%d"),
            "demand_tons": float(demand[i]),
            "capacity_utilization_pct": float(demand[i] / nominal_capacity * 100),
            "slack_time_pct": float(slack),
            "fragility_score": float(score),
            "fragility_level": level
        })
    
    # Capacity utilization analysis
    capacity_analysis = analyze_capacity_utilization(df, nominal_capacity)
    
    # What-if scenarios
    logger.info("Simulating demand scenarios...")
    scenarios = {}
    
    for scenario_type in ["surge", "drop", "volatility"]:
        for magnitude in [0.1, 0.2] if scenario_type != "volatility" else [0.15]:
            scenario_name = f"{scenario_type}_{int(magnitude*100)}pct"
            df_scenario = simulate_demand_shock(df, scenario_type, magnitude)
            
            scenario_fragility = []
            for i in range(len(df_scenario)):
                vol = df_scenario["cargo_tons"].iloc[max(0, i-7):i].std() if i > 0 else 0
                score = compute_fragility_score(
                    df_scenario["cargo_tons"].iloc[i],
                    vol,
                    nominal_capacity,
                    df_scenario["cargo_tons"].mean(),
                    df_scenario["cargo_tons"].std()
                )
                scenario_fragility.append(float(score))
            
            scenarios[scenario_name] = {
                "avg_fragility_score": float(np.mean(scenario_fragility)),
                "max_fragility_score": float(np.max(scenario_fragility)),
                "avg_demand": float(df_scenario["cargo_tons"].mean()),
                "capacity_util_pct": float(df_scenario["cargo_tons"].mean() / nominal_capacity * 100),
            }
    
    # Summary statistics
    summary = {
        "analysis_date": pd.Timestamp.now().isoformat(),
        "nominal_capacity": float(nominal_capacity),
        "mean_fragility_score": float(np.mean([fs["fragility_score"] for fs in fragility_scores])),
        "max_fragility_score": float(np.max([fs["fragility_score"] for fs in fragility_scores])),
        "fragile_days": int(sum(1 for fs in fragility_scores if fs["fragility_level"] in ["fragile", "critical"])),
        "total_days": len(df),
    }
    
    # Save results
    FRAGILITY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results = {
        "summary": summary,
        "capacity_utilization": capacity_analysis,
        "daily_fragility_scores": fragility_scores,
        "what_if_scenarios": scenarios
    }
    
    with open(FRAGILITY_REPORT_PATH, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved schedule fragility analysis to {FRAGILITY_REPORT_PATH}")
    
    # Print summary report
    print("\n" + "="*70)
    print("📉 SCHEDULE FRAGILITY & WHAT-IF ANALYSIS REPORT")
    print("="*70)
    
    print(f"\n📊 Capacity Utilization:")
    print(f"  Nominal Capacity: {capacity_analysis['nominal_capacity']:.0f} tons")
    print(f"  Mean Utilization: {capacity_analysis['mean_utilization']:.1f}%")
    print(f"  Max Utilization: {capacity_analysis['max_utilization']:.1f}%")
    print(f"  Days > 90% Util: {capacity_analysis['days_over_90_pct']}")
    print(f"  Days > 80% Util: {capacity_analysis['days_over_80_pct']}")
    
    print(f"\n🚨 Schedule Fragility:")
    print(f"  Avg Fragility Score: {summary['mean_fragility_score']:.1f} / 100")
    print(f"  Max Fragility Score: {summary['max_fragility_score']:.1f} / 100")
    print(f"  Fragile/Critical Days: {summary['fragile_days']} / {summary['total_days']}")
    
    print(f"\n🔮 What-If Scenarios (Avg Fragility Impact):")
    for scenario, metrics in scenarios.items():
        print(f"  {scenario}: Fragility={metrics['avg_fragility_score']:.1f}, Util={metrics['capacity_util_pct']:.1f}%")
    
    print(f"\n✅ Schedule fragility analysis complete!")
    print(f"   Recommend: Review operational strategies for fragile days.\n")


if __name__ == "__main__":
    run_schedule_fragility_analysis()
