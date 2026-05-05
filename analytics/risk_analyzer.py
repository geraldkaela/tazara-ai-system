"""Risk and duration analysis for cargo demand and scheduling.

Analyzes cargo demand patterns to identify:
- High-volatility periods
- Bottleneck risk zones
- Schedule fragility factors
- Duration uncertainty estimates

Outputs risk scores and recommendations for operational planning.

Usage:
    python -m analytics.risk_analyzer
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


def compute_volatility(series: pd.Series, window: int = 7) -> pd.Series:
    """Compute rolling volatility (standard deviation)."""
    return series.rolling(window).std()


def compute_trend(series: pd.Series, window: int = 14) -> pd.Series:
    """Compute rolling trend direction (slope)."""
    return series.rolling(window).apply(
        lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0,
        raw=False
    )


def detect_anomalies(series: pd.Series, threshold: float = 2.0) -> np.ndarray:
    """Detect anomalies using z-score (values beyond ±threshold std devs)."""
    mean = series.mean()
    std = series.std()
    z_scores = np.abs((series - mean) / std)
    return z_scores > threshold


def compute_risk_score(
    demand: float,
    volatility: float,
    trend: float,
    is_anomaly: bool,
    mean_demand: float,
    std_demand: float
) -> float:
    """
    Compute composite risk score (0-100).
    Higher score = higher risk.
    """
    score = 0.0
    
    # Demand level risk (0-20): high demand periods are riskier
    demand_pct = (demand - mean_demand) / max(std_demand, 1.0)
    score += min(20, max(0, 10 + demand_pct * 5))
    
    # Volatility risk (0-30): high volatility = harder to forecast accurately
    vol_score = min(30, volatility * 10)
    score += vol_score
    
    # Trend risk (0-20): sharp upward trends increase scheduling pressure
    trend_score = min(20, max(0, abs(trend) * 5))
    score += trend_score
    
    # Anomaly risk (0-30): detected anomalies add risk
    if is_anomaly:
        score += 30
    
    return min(100, score)


def classify_risk_level(score: float) -> str:
    """Classify risk score into categorical level."""
    if score < 25:
        return "low"
    elif score < 50:
        return "medium"
    elif score < 75:
        return "high"
    else:
        return "critical"


def estimate_duration_uncertainty(volatility: float, trend_magnitude: float) -> Dict[str, float]:
    """
    Estimate scheduling duration uncertainty based on demand patterns.
    Returns bounds around nominal duration.
    """
    # Base uncertainty from volatility
    volatility_factor = min(0.4, volatility / 100.0)  # up to 40% from volatility
    
    # Trend factor (sudden changes make scheduling less predictable)
    trend_factor = min(0.2, abs(trend_magnitude) * 0.05)  # up to 20% from trend
    
    total_uncertainty = volatility_factor + trend_factor
    
    return {
        "lower_bound_pct": -total_uncertainty * 100,  # % reduction in duration
        "upper_bound_pct": total_uncertainty * 100,   # % increase in duration
        "uncertainty_level": "low" if total_uncertainty < 0.1 else "medium" if total_uncertainty < 0.3 else "high"
    }


def detect_bottleneck_periods(
    df: pd.DataFrame,
    high_demand_threshold: float = None,
    volatility_threshold: float = None
) -> List[Dict]:
    """
    Detect periods of potential scheduling bottlenecks.
    Bottlenecks occur when demand is high AND volatile.
    """
    if high_demand_threshold is None:
        high_demand_threshold = df["cargo_tons"].quantile(0.75)
    if volatility_threshold is None:
        volatility_threshold = df["cargo_tons"].std() * 0.8
    
    df = df.copy()
    df["volatility"] = compute_volatility(df["cargo_tons"], window=7)
    df["is_bottleneck"] = (
        (df["cargo_tons"] > high_demand_threshold) &
        (df["volatility"] > volatility_threshold)
    )
    
    bottlenecks = []
    in_bottleneck = False
    start_idx = None
    
    for idx, row in df.iterrows():
        if row["is_bottleneck"] and not in_bottleneck:
            in_bottleneck = True
            start_idx = idx
        elif not row["is_bottleneck"] and in_bottleneck:
            # End of bottleneck period
            bottlenecks.append({
                "start_date": df.iloc[start_idx]["date"].strftime("%Y-%m-%d"),
                "end_date": df.iloc[idx-1]["date"].strftime("%Y-%m-%d") if idx > 0 else str(df.iloc[idx]["date"]),
                "duration_days": int(idx - start_idx),
                "avg_demand": float(df.iloc[start_idx:idx]["cargo_tons"].mean()),
                "max_demand": float(df.iloc[start_idx:idx]["cargo_tons"].max()),
                "avg_volatility": float(df.iloc[start_idx:idx]["volatility"].mean())
            })
            in_bottleneck = False
    
    return bottlenecks


def run_risk_analysis() -> None:
    """Run full risk and duration analysis."""
    logger.info("Starting risk and duration analysis...")
    
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Features file not found: {FEATURES_PATH}")
    
    df = pd.read_csv(FEATURES_PATH, parse_dates=["date"])
    logger.info(f"Loaded {len(df)} records for risk analysis")
    
    # Compute risk metrics
    demand = df["cargo_tons"].values
    mean_demand = demand.mean()
    std_demand = demand.std()
    
    volatility = compute_volatility(df["cargo_tons"], window=7).fillna(0).values
    trend = compute_trend(df["cargo_tons"], window=14).fillna(0).values
    anomalies = detect_anomalies(df["cargo_tons"], threshold=2.0).values
    
    # Compute per-day risk scores
    risk_scores = []
    for i in range(len(df)):
        score = compute_risk_score(
            demand[i],
            volatility[i],
            trend[i],
            anomalies[i],
            mean_demand,
            std_demand
        )
        risk_level = classify_risk_level(score)
        duration_uncertainty = estimate_duration_uncertainty(volatility[i], trend[i])
        
        risk_scores.append({
            "date": df.iloc[i]["date"].strftime("%Y-%m-%d"),
            "demand_tons": float(demand[i]),
            "volatility": float(volatility[i]),
            "trend": float(trend[i]),
            "is_anomaly": bool(anomalies[i]),
            "risk_score": float(score),
            "risk_level": risk_level,
            "duration_uncertainty_pct": {
                "lower": float(duration_uncertainty["lower_bound_pct"]),
                "upper": float(duration_uncertainty["upper_bound_pct"])
            }
        })
    
    # Detect bottleneck periods
    bottlenecks = detect_bottleneck_periods(df)
    
    # Compile summary statistics
    summary = {
        "analysis_date": pd.Timestamp.now().isoformat(),
        "total_days_analyzed": int(len(df)),
        "mean_demand": float(mean_demand),
        "std_demand": float(std_demand),
        "cv": float(std_demand / mean_demand) if mean_demand > 0 else 0,  # coefficient of variation
        "high_risk_days": int(sum(1 for r in risk_scores if r["risk_level"] in ["high", "critical"])),
        "anomaly_days": int(anomalies.sum()),
        "num_bottleneck_periods": int(len(bottlenecks)),
        "avg_risk_score": float(np.mean([r["risk_score"] for r in risk_scores])),
        "max_risk_score": float(np.max([r["risk_score"] for r in risk_scores])),
    }
    
    # Save analysis
    RISK_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    analysis_result = {
        "summary": summary,
        "daily_risk_scores": risk_scores,
        "bottleneck_periods": bottlenecks,
    }
    
    with open(RISK_REPORT_PATH, "w") as f:
        json.dump(analysis_result, f, indent=2)
    logger.info(f"Saved risk analysis to {RISK_REPORT_PATH}")
    
    # Print summary report
    print("\n" + "="*70)
    print("⚠️  RISK & DURATION ANALYSIS REPORT")
    print("="*70)
    print(f"\n📊 Demand Characteristics:")
    print(f"  Mean:  {summary['mean_demand']:.2f} tons")
    print(f"  Std:   {summary['std_demand']:.2f} tons")
    print(f"  CV:    {summary['cv']:.4f} (Coefficient of Variation)")
    
    print(f"\n🚨 Risk Summary:")
    print(f"  High/Critical Risk Days: {summary['high_risk_days']} / {summary['total_days_analyzed']}")
    print(f"  Anomaly Days: {summary['anomaly_days']}")
    print(f"  Avg Risk Score: {summary['avg_risk_score']:.2f} / 100")
    print(f"  Max Risk Score: {summary['max_risk_score']:.2f} / 100")
    
    print(f"\n🔴 Bottleneck Periods: {summary['num_bottleneck_periods']} detected")
    for i, bn in enumerate(bottlenecks[:3]):
        print(f"  {i+1}. {bn['start_date']} to {bn['end_date']} ({bn['duration_days']} days)")
        print(f"     Avg Demand: {bn['avg_demand']:.2f} tons, Max: {bn['max_demand']:.2f} tons")
    
    print(f"\n✅ Risk analysis complete!")
    print(f"   Recommend: Monitor {summary['high_risk_days']} high-risk days closely for scheduling.\n")


if __name__ == "__main__":
    run_risk_analysis()
