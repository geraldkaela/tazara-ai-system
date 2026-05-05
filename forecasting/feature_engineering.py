"""Feature engineering utilities for demand forecasting.

Creates lag and rolling statistics, calendar features, and writes a
feature CSV to `data/processed/features.csv`.

Usage:
    python -m forecasting.feature_engineering
"""
from __future__ import annotations

from pathlib import Path
import logging
import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


INPUT = Path("data/simulated/cargo_demand.csv")
OUTPUT = Path("data/processed/features.csv")


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    else:
        df.index = pd.to_datetime(df.index)
        df = df.reset_index().rename(columns={"index": "date"})

    df = df.sort_values("date")
    df = df.set_index("date").asfreq("D")

    # Ensure target exists
    if "cargo_tons" not in df.columns:
        raise ValueError("Expected 'cargo_tons' column in input data")

    # Lags
    for lag in (1, 7, 14, 28):
        df[f"lag_{lag}"] = df["cargo_tons"].shift(lag)

    # Rolling statistics
    df["roll_mean_7"] = df["cargo_tons"].rolling(7, min_periods=1).mean()
    df["roll_std_7"] = df["cargo_tons"].rolling(7, min_periods=1).std().fillna(0)
    df["roll_mean_30"] = df["cargo_tons"].rolling(30, min_periods=1).mean()

    # Percent change
    df["pct_change_1"] = df["cargo_tons"].pct_change().fillna(0)

    # Calendar features
    df["dayofweek"] = df.index.dayofweek
    df["month"] = df.index.month
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)

    # Fill remaining NaNs conservatively
    df = df.fillna(method="ffill").fillna(0)

    return df.reset_index()


def run(in_path: Path = INPUT, out_path: Path = OUTPUT) -> Path:
    if not in_path.exists():
        raise FileNotFoundError(f"Input data not found: {in_path}")
    df = pd.read_csv(in_path, parse_dates=["date"]) if in_path.exists() else pd.DataFrame()
    if df.empty:
        raise ValueError(f"Input data is empty: {in_path}")
    feats = create_features(df)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    feats.to_csv(out_path, index=False)
    logger.info(f"Wrote features to {out_path} ({len(feats)} rows, {len(feats.columns)} cols)")
    return out_path


if __name__ == "__main__":
    run()
