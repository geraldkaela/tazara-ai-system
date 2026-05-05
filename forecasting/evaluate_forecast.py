"""Forecast validation and backtesting framework for Phase 2.

Provides utilities for:
- Computing accuracy metrics (RMSE, MAE, MAPE, R²)
- Time-series cross-validation (rolling window backtests)
- Forecast skill assessment
- Comparison of competing models

Usage:
    python -m forecasting.evaluate_forecast
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple, List, Dict
import json

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


FEATURES_PATH = Path("data/processed/features.csv")
METRICS_PATH = Path("metrics/backtest_results.json")


def mean_absolute_percentage_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute MAPE, handling zero values gracefully."""
    mask = y_true != 0
    if mask.sum() == 0:
        return 0.0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute comprehensive accuracy metrics."""
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    return {
        "rmse": float(rmse),
        "mae": float(mae),
        "mape": float(mape),
        "r2": float(r2),
        "mse": float(mse),
    }


def rolling_window_backtest(
    y: np.ndarray,
    train_size: int = 100,
    test_size: int = 20,
    step_size: int = 10
) -> Tuple[List[dict], dict]:
    """
    Perform rolling window backtests on historical data.
    
    Args:
        y: Target time series
        train_size: Size of training window
        test_size: Size of test window
        step_size: Number of steps to advance each iteration
    
    Returns:
        List of per-window metrics and overall aggregate metrics
    """
    results = []
    all_y_true = []
    all_y_pred = []
    
    for start in range(0, len(y) - train_size - test_size, step_size):
        train_end = start + train_size
        test_start = train_end
        test_end = test_start + test_size
        
        y_train = y[start:train_end]
        y_test = y[test_start:test_end]
        
        # Simple baseline: use mean of training data for all predictions
        baseline_pred = np.full(len(y_test), y_train.mean())
        
        # Metrics for this window
        metrics = compute_metrics(y_test, baseline_pred)
        metrics["window"] = len(results) + 1
        metrics["train_start"] = start
        metrics["train_end"] = train_end
        metrics["test_start"] = test_start
        metrics["test_end"] = test_end
        
        results.append(metrics)
        all_y_true.extend(y_test)
        all_y_pred.extend(baseline_pred)
    
    # Aggregate metrics across all windows
    aggregate = compute_metrics(np.array(all_y_true), np.array(all_y_pred))
    aggregate["num_windows"] = len(results)
    aggregate["total_test_samples"] = len(all_y_true)
    
    return results, aggregate


def load_and_prepare_data() -> np.ndarray:
    """Load features and return target time series."""
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Features file not found: {FEATURES_PATH}")
    
    df = pd.read_csv(FEATURES_PATH, parse_dates=["date"])
    y = df["cargo_tons"].values.astype(float)
    logger.info(f"Loaded {len(y)} samples for backtesting")
    return y


def run_validation() -> None:
    """Run full validation suite and save results."""
    logger.info("Starting forecast validation and backtesting...")
    
    y = load_and_prepare_data()
    
    # Rolling window backtest
    logger.info("Running rolling window backtests...")
    window_results, aggregate = rolling_window_backtest(y, train_size=100, test_size=20, step_size=10)
    
    # Save results
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    backtest_results = {
        "validation_framework": "rolling_window_backtest",
        "timestamp": pd.Timestamp.now().isoformat(),
        "aggregate_metrics": aggregate,
        "window_results": window_results,
    }
    
    with open(METRICS_PATH, "w") as f:
        json.dump(backtest_results, f, indent=2)
    logger.info(f"Saved backtest results to {METRICS_PATH}")
    
    # Print summary
    print("\n" + "="*70)
    print("🔍 FORECAST VALIDATION & BACKTESTING REPORT")
    print("="*70)
    print(f"\n📊 Aggregate Metrics Across {aggregate['num_windows']} Windows:")
    print(f"  RMSE:  {aggregate['rmse']:.4f}")
    print(f"  MAE:   {aggregate['mae']:.4f}")
    print(f"  MAPE:  {aggregate['mape']:.2f}%")
    print(f"  R²:    {aggregate['r2']:.4f}")
    print(f"  Total Test Samples: {aggregate['total_test_samples']}")
    
    print(f"\n📈 Per-Window Results (first 5 windows):")
    for i, wr in enumerate(window_results[:5]):
        print(f"  Window {wr['window']}: RMSE={wr['rmse']:.4f}, MAE={wr['mae']:.4f}, R²={wr['r2']:.4f}")
    
    # Skill assessment
    print(f"\n✅ Validation complete!")
    print(f"   Baseline (mean forecast) MAPE: {aggregate['mape']:.2f}%")
    print(f"   Recommend next: Compare LSTM predictions vs. baseline in production.\n")


if __name__ == "__main__":
    run_validation()
